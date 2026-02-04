"""SQL Agent with Dynamic Few-Shot for admission score queries."""

import json
import logging
import re
from typing import Any, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from src.core.config import settings
from src.core.embeddings import get_embedding_service
from src.core.llm import get_llm_service
from src.database.postgres import get_postgres_db
from src.database.qdrant import get_qdrant_db
from src.utils.vietnamese import VietnameseTextProcessor

logger = logging.getLogger(__name__)


# SQL generation system prompt
SQL_SYSTEM_PROMPT = """Bạn là chuyên gia SQL cho hệ thống tra cứu điểm chuẩn tuyển sinh quân sự Việt Nam.

## Schema Database:
- truong(id, ma_truong, ten_truong, ten_khong_dau, loai_truong, dia_chi, website)
- nganh(id, truong_id, ma_nganh, ten_nganh, ten_khong_dau)
- khoi_thi(id, ma_khoi, ten_khoi, mon_hoc)
- diem_chuan(id, nganh_id, khoi_thi_id, nam, diem_chuan, chi_tieu, gioi_tinh, khu_vuc, doi_tuong, ghi_chu)

## View có sẵn:
- view_tra_cuu_diem: JOIN sẵn các bảng với các cột (diem_chuan_id, ma_truong, ten_truong, loai_truong, ma_nganh, ten_nganh, ma_khoi, ten_khoi, mon_hoc, nam, diem_chuan, chi_tieu, gioi_tinh, khu_vuc, doi_tuong, ghi_chu)

## Quy tắc:
1. Luôn sử dụng view_tra_cuu_diem cho các truy vấn điểm chuẩn
2. Sử dụng hàm unaccent() hoặc cột ten_khong_dau để tìm kiếm tiếng Việt không dấu
3. Sử dụng ILIKE với % để tìm kiếm gần đúng
4. Mặc định lấy năm gần nhất nếu không chỉ định năm
5. Giới hạn kết quả với LIMIT để tránh trả về quá nhiều dữ liệu
6. CHỈ trả về câu SQL, không giải thích

## Lưu ý về tìm kiếm tên:
- Người dùng có thể nhập không dấu: "hoc vien ky thuat quan su"
- Sử dụng: LOWER(unaccent(ten_truong)) LIKE LOWER(unaccent('%input%'))
- Hoặc: ten_khong_dau LIKE '%input%'"""


# SQL validation prompt
SQL_VALIDATION_PROMPT = """Kiểm tra câu SQL sau có hợp lệ và an toàn không.

SQL: {sql}

Trả về JSON:
{{"valid": true/false, "error": "mô tả lỗi nếu có", "suggestion": "gợi ý sửa nếu có"}}

Kiểm tra:
1. Không có DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE
2. Cú pháp đúng
3. Tên bảng/cột hợp lệ
4. Có LIMIT để tránh quá nhiều kết quả"""


class SQLAgent:
    """SQL Agent with dynamic few-shot example selection."""

    def __init__(
        self,
        max_retries: int = 3,
        few_shot_count: int = 5,
    ):
        """Initialize SQL Agent.

        Args:
            max_retries: Maximum SQL generation retries.
            few_shot_count: Number of few-shot examples to include.
        """
        self.max_retries = max_retries
        self.few_shot_count = few_shot_count
        self.llm_service = get_llm_service()
        self.embedding_service = get_embedding_service()
        self.db = get_postgres_db()
        self.qdrant = get_qdrant_db()
        self.text_processor = VietnameseTextProcessor()

    async def process_query(
        self,
        user_query: str,
        context: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Process a natural language query and return SQL results.

        Args:
            user_query: User's question in natural language.
            context: Optional context from conversation.

        Returns:
            Dictionary with query, sql, results, and answer.
        """
        logger.info(f"Processing SQL query: {user_query}")

        # Extract entities from query
        entities = self._extract_entities(user_query)
        logger.debug(f"Extracted entities: {entities}")

        # Get similar few-shot examples
        examples = await self._get_few_shot_examples(user_query)

        # Generate SQL with retries
        sql = None
        error_history = []

        for attempt in range(self.max_retries):
            try:
                # Generate SQL
                sql = await self._generate_sql(
                    user_query, examples, entities, error_history
                )
                logger.debug(f"Generated SQL (attempt {attempt + 1}): {sql}")

                # Validate SQL
                is_valid, validation_error = await self._validate_sql(sql)
                if not is_valid:
                    error_history.append(f"Validation error: {validation_error}")
                    continue

                # Execute SQL
                results = await self._execute_sql(sql)

                # Generate natural language answer
                answer = await self._generate_answer(user_query, results, entities)

                return {
                    "query": user_query,
                    "sql": sql,
                    "results": results,
                    "answer": answer,
                    "entities": entities,
                    "attempts": attempt + 1,
                }

            except Exception as e:
                error_history.append(str(e))
                logger.warning(f"SQL attempt {attempt + 1} failed: {e}")

        # All retries failed
        return {
            "query": user_query,
            "sql": sql,
            "results": None,
            "answer": "Xin lỗi, tôi không thể xử lý truy vấn này. Vui lòng thử lại với câu hỏi khác.",
            "error": error_history[-1] if error_history else "Unknown error",
            "entities": entities,
            "attempts": self.max_retries,
        }

    def _extract_entities(self, query: str) -> dict[str, Any]:
        """Extract entities from query.

        Args:
            query: User query.

        Returns:
            Extracted entities.
        """
        entities = {}

        # Extract year
        year = self.text_processor.extract_year(query)
        if year:
            entities["year"] = year

        # Extract score
        score = self.text_processor.extract_score(query)
        if score:
            entities["score"] = score

        # Extract khoi thi
        khoi = self.text_processor.extract_khoi_thi(query)
        if khoi:
            entities["khoi_thi"] = khoi

        # Normalize query for search
        entities["query_normalized"] = self.text_processor.normalize_text(query)

        return entities

    async def _get_few_shot_examples(self, query: str) -> list[dict]:
        """Get relevant few-shot examples using semantic search.

        Args:
            query: User query.

        Returns:
            List of relevant examples.
        """
        try:
            # Embed query
            query_embedding = self.embedding_service.encode_query(query)

            # Search for similar examples
            results = await self.qdrant.search(
                collection_name=settings.qdrant_sql_examples_collection,
                query_vector=query_embedding.tolist(),
                limit=self.few_shot_count,
                score_threshold=0.5,
            )

            examples = []
            for result in results:
                payload = result.get("payload", {})
                examples.append({
                    "question": payload.get("question", ""),
                    "sql": payload.get("sql", ""),
                    "score": result.get("score", 0),
                })

            return examples

        except Exception as e:
            logger.warning(f"Failed to get few-shot examples: {e}")
            return self._get_default_examples()

    def _get_default_examples(self) -> list[dict]:
        """Get default few-shot examples when semantic search fails."""
        return [
            {
                "question": "Điểm chuẩn Học viện Kỹ thuật Quân sự năm 2024?",
                "sql": """SELECT ten_truong, ten_nganh, ma_khoi, diem_chuan, chi_tieu
FROM view_tra_cuu_diem
WHERE ten_khong_dau LIKE '%hoc vien ky thuat quan su%' AND nam = 2024
ORDER BY ten_nganh, ma_khoi;""",
            },
            {
                "question": "Với 25 điểm khối A, tôi có thể vào trường nào năm 2024?",
                "sql": """SELECT DISTINCT ten_truong, ten_nganh, ma_khoi, diem_chuan
FROM view_tra_cuu_diem
WHERE diem_chuan <= 25 AND ma_khoi = 'A00' AND nam = 2024
ORDER BY diem_chuan DESC
LIMIT 20;""",
            },
            {
                "question": "So sánh điểm chuẩn các trường quân đội năm 2023 và 2024?",
                "sql": """SELECT ten_truong, ten_nganh, ma_khoi,
    MAX(CASE WHEN nam = 2023 THEN diem_chuan END) as diem_2023,
    MAX(CASE WHEN nam = 2024 THEN diem_chuan END) as diem_2024
FROM view_tra_cuu_diem
WHERE nam IN (2023, 2024) AND loai_truong = 'quan_doi'
GROUP BY ten_truong, ten_nganh, ma_khoi
ORDER BY ten_truong, ten_nganh;""",
            },
        ]

    async def _generate_sql(
        self,
        query: str,
        examples: list[dict],
        entities: dict,
        error_history: list[str],
    ) -> str:
        """Generate SQL from natural language query.

        Args:
            query: User query.
            examples: Few-shot examples.
            entities: Extracted entities.
            error_history: Previous errors for self-correction.

        Returns:
            Generated SQL query.
        """
        # Build examples section
        examples_text = "\n\n".join([
            f"Câu hỏi: {ex['question']}\nSQL: {ex['sql']}"
            for ex in examples
        ])

        # Build error correction context
        error_context = ""
        if error_history:
            error_context = f"\n\nCác lỗi trước đó cần tránh:\n" + "\n".join(
                f"- {err}" for err in error_history[-3:]
            )

        # Build entity context
        entity_context = ""
        if entities:
            parts = []
            if "year" in entities:
                parts.append(f"Năm: {entities['year']}")
            if "score" in entities:
                parts.append(f"Điểm: {entities['score']}")
            if "khoi_thi" in entities:
                parts.append(f"Khối: {entities['khoi_thi']}")
            if parts:
                entity_context = f"\n\nThông tin trích xuất: {', '.join(parts)}"

        prompt = f"""## Ví dụ:
{examples_text}

{error_context}
{entity_context}

## Câu hỏi cần trả lời:
{query}

## SQL:"""

        response = await self.llm_service.generate(
            prompt=prompt,
            system_prompt=SQL_SYSTEM_PROMPT,
        )

        # Extract SQL from response
        sql = self._extract_sql(response)
        return sql

    def _extract_sql(self, response: str) -> str:
        """Extract SQL query from LLM response.

        Args:
            response: LLM response text.

        Returns:
            Extracted SQL query.
        """
        # Remove markdown code blocks
        response = response.strip()

        # Remove thinking tags (qwen3, deepseek-r1 models)
        response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)
        response = response.strip()

        if response.startswith("```sql"):
            response = response[6:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        # Find SELECT statement
        sql_match = re.search(
            r"(SELECT\s+.+?)(?:;|$)",
            response,
            re.IGNORECASE | re.DOTALL,
        )

        if sql_match:
            return sql_match.group(1).strip() + ";"

        return response.strip()

    async def _validate_sql(self, sql: str) -> tuple[bool, Optional[str]]:
        """Validate SQL query for safety and correctness.

        Args:
            sql: SQL query to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        # Basic safety checks
        dangerous_keywords = [
            "DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
            "TRUNCATE", "CREATE", "GRANT", "REVOKE", "--", "/*",
        ]

        sql_upper = sql.upper()
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return False, f"Dangerous keyword detected: {keyword}"

        # Must be a SELECT query
        if not sql_upper.strip().startswith("SELECT"):
            return False, "Query must start with SELECT"

        # Use LLM for deeper validation
        try:
            prompt = SQL_VALIDATION_PROMPT.format(sql=sql)
            response = await self.llm_service.generate_with_json(
                prompt=prompt,
                use_grader=True,
            )

            if not response.get("valid", False):
                return False, response.get("error", "Validation failed")

            return True, None

        except Exception as e:
            logger.warning(f"SQL validation error: {e}")
            # Allow through if validation fails but basic checks pass
            return True, None

    async def _execute_sql(self, sql: str) -> list[dict]:
        """Execute SQL query safely.

        Args:
            sql: SQL query to execute.

        Returns:
            Query results as list of dictionaries.
        """
        # Ensure query has LIMIT
        if "LIMIT" not in sql.upper():
            sql = sql.rstrip(";") + " LIMIT 50;"

        results = await self.db.fetch_all(sql)
        return results

    async def _generate_answer(
        self,
        query: str,
        results: list[dict],
        entities: dict,
    ) -> str:
        """Generate natural language answer from SQL results.

        Args:
            query: Original user query.
            results: SQL query results.
            entities: Extracted entities.

        Returns:
            Natural language answer.
        """
        if not results:
            return "Không tìm thấy dữ liệu phù hợp với yêu cầu của bạn."

        # Format results for LLM
        results_text = json.dumps(results[:10], ensure_ascii=False, indent=2)

        prompt = f"""Dựa trên kết quả truy vấn sau, hãy trả lời câu hỏi của người dùng bằng tiếng Việt một cách tự nhiên và dễ hiểu.

Câu hỏi: {query}

Kết quả truy vấn:
{results_text}

Số kết quả tổng: {len(results)}

Hãy trả lời ngắn gọn, đầy đủ thông tin quan trọng. Nếu có nhiều kết quả, hãy tóm tắt theo nhóm."""

        answer = await self.llm_service.generate(
            prompt=prompt,
            system_prompt="Bạn là trợ lý tư vấn tuyển sinh quân sự. Trả lời chính xác dựa trên dữ liệu được cung cấp.",
        )

        return answer


# Factory function
def get_sql_agent() -> SQLAgent:
    """Get SQL Agent instance."""
    return SQLAgent(
        max_retries=settings.sql_max_retries,
        few_shot_count=settings.sql_few_shot_examples,
    )
