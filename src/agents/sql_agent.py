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

## QUAN TRỌNG: Chỉ sử dụng view_tra_cuu_diem, KHÔNG truy vấn trực tiếp các bảng gốc.

## Các cột trong view_tra_cuu_diem:
| Cột | Kiểu | Mô tả | Ví dụ |
|-----|------|--------|-------|
| diem_chuan_id | int | ID bản ghi | 1 |
| ma_truong | text | Mã trường | 'HVKTQS' |
| ten_truong | text | Tên trường (có dấu) | 'Học viện Kỹ thuật Quân sự' |
| ten_khong_dau | text | Tên trường không dấu | 'hoc vien ky thuat quan su' |
| loai_truong | text | Mã loại trường | 'HVKTQS' |
| ma_nganh | text | Mã ngành | 'CN01' |
| ten_nganh | text | Tên ngành | 'Công nghệ thông tin' |
| ten_nganh_khong_dau | text | Tên ngành không dấu | 'cong nghe thong tin' |
| ma_khoi | text | Mã khối thi | 'A00', 'A01', 'B00' |
| ten_khoi | text | Tên khối thi | 'Toán-Lý-Hóa' |
| mon_hoc | text | Các môn học trong khối | 'Toán, Lý, Hóa' |
| nam | int | Năm tuyển sinh | 2024 |
| diem_chuan | float | Điểm chuẩn | 26.5 |
| chi_tieu | int | Chỉ tiêu tuyển | 50 |
| gioi_tinh | text | Giới tính — GIÁ TRỊ THỰC TẾ: 'nam' hoặc 'nu' (KHÔNG dùng 'Nam'/'Nữ'/'NAM'/'NỮ') | 'nam' |
| khu_vuc | text | Khu vực — GIÁ TRỊ THỰC TẾ: 'mien_bac' hoặc 'mien_nam' (KHÔNG dùng 'KV1'/'KV2'/'Miền Bắc') | 'mien_bac' |
| doi_tuong | text | Đối tượng | 'DT1' |
| ghi_chu | text | Ghi chú | |

## Quy tắc BẮT BUỘC:
1. LUÔN dùng view_tra_cuu_diem. KHÔNG dùng bảng gốc (truong, nganh, khoi_thi, diem_chuan)
2. Lọc khối thi bằng: ma_khoi = 'A01' (KHÔNG dùng khoi_thi_id)
3. **Lọc trường bằng ten_khong_dau** (KHÔNG dùng ma_truong, loai_truong, truong_id, nganh_id):
   - ĐÚNG: ten_khong_dau ILIKE '%hoc vien hai quan%'
   - SAI: ma_truong ILIKE '%hoc vien hai quan%'
4. **Lọc ngành bằng ten_nganh_khong_dau** (KHÔNG dùng ma_nganh để tìm theo tên):
   - ĐÚNG: ten_nganh_khong_dau ILIKE '%cong nghe thong tin%'
5. Sử dụng ILIKE với % để tìm kiếm gần đúng
6. Mặc định lấy năm gần nhất nếu không chỉ định năm
7. Giới hạn kết quả với LIMIT để tránh trả về quá nhiều dữ liệu
8. CHỈ trả về câu SQL, không giải thích
9. Khi người dùng hỏi "có đỗ trường X không" hoặc "X điểm vào trường Y được không", hãy lấy điểm chuẩn của trường Y để so sánh, KHÔNG lọc theo diem_chuan <= X
10. **CHỈ lọc theo khối (ma_khoi) khi người dùng NÊU RÕ khối thi**. Nếu hỏi "các ngành" hoặc "điểm chuẩn trường X" mà KHÔNG nói khối cụ thể → KHÔNG thêm WHERE ma_khoi
11. **LUÔN SELECT đủ các cột**: nam, ten_truong, ten_nganh, ma_khoi, gioi_tinh, khu_vuc, diem_chuan, chi_tieu. KHÔNG được bỏ cột nào trong số này khỏi SELECT
12. **Giá trị lọc gioi_tinh**: dùng 'nam' cho nam, 'nu' cho nữ — TUYỆT ĐỐI không dùng 'Nam'/'Nữ'/'NAM'/'NỮ'
13. **Giá trị lọc khu_vuc**: dùng 'mien_bac' hoặc 'mien_nam' — TUYỆT ĐỐI không dùng 'KV1'/'KV2'/'Miền Bắc'
14. Khi hỏi "qua các năm" hoặc so sánh nhiều năm: KHÔNG thêm WHERE nam = ..., trả về tất cả năm và ORDER BY nam ASC

## Ví dụ ĐÚNG/SAI:

Câu hỏi: "Điểm chuẩn nữ học viện kỹ thuật quân sự qua các năm"
- SAI: WHERE gioi_tinh = 'Nữ' (sai giá trị)
- SAI: WHERE gioi_tinh = 'Nu' (sai giá trị)
- SAI: WHERE gioi_tinh = 'Nam' (sai - đây là nữ)
- ĐÚNG: SELECT nam, ten_truong, ten_nganh, ma_khoi, gioi_tinh, khu_vuc, diem_chuan, chi_tieu FROM view_tra_cuu_diem WHERE ten_khong_dau ILIKE '%hoc vien ky thuat quan su%' AND gioi_tinh = 'nu' ORDER BY nam ASC, ten_nganh, khu_vuc LIMIT 100;

Câu hỏi: "Điểm chuẩn các ngành của học viện hải quân năm 2025"
- SAI: SELECT ten_nganh, ma_khoi, diem_chuan FROM view_tra_cuu_diem ... (thiếu nam, gioi_tinh, khu_vuc)
- ĐÚNG: SELECT nam, ten_truong, ten_nganh, ma_khoi, gioi_tinh, khu_vuc, diem_chuan, chi_tieu FROM view_tra_cuu_diem WHERE ten_khong_dau ILIKE '%hoc vien hai quan%' AND nam = 2025 ORDER BY ten_nganh, ma_khoi, khu_vuc LIMIT 100;

Câu hỏi: "Điểm chuẩn miền bắc năm 2024"
- SAI: WHERE khu_vuc = 'Miền Bắc' (sai giá trị)
- SAI: WHERE khu_vuc = 'KV1' (sai giá trị)
- ĐÚNG: WHERE khu_vuc = 'mien_bac' AND nam = 2024

## Lưu ý về tìm kiếm tên:
- Người dùng có thể nhập không dấu: "hoc vien ky thuat quan su"
- Sử dụng: ten_khong_dau ILIKE '%hoc vien ky thuat quan su%'"""


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
        print(f"[SQL] Full query: {user_query}", flush=True)

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
                # Fix filter values LLM commonly gets wrong (gioi_tinh, khu_vuc)
                sql = self._fix_filter_values(sql, entities)
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

        # Extract gender (must be before normalize to preserve diacritics)
        query_lower = query.lower()
        if any(w in query_lower for w in ["nữ", "nu gioi", "nữ giới", "con gái", "female"]):
            entities["gioi_tinh"] = "nu"
        elif any(w in query_lower for w in ["nam giới", "con trai", "male"]):
            entities["gioi_tinh"] = "nam"

        # Extract khu_vuc
        if any(w in query_lower for w in ["miền bắc", "mien bac", "phía bắc"]):
            entities["khu_vuc"] = "mien_bac"
        elif any(w in query_lower for w in ["miền nam", "mien nam", "phía nam"]):
            entities["khu_vuc"] = "mien_nam"

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
                "sql": """SELECT nam, ten_truong, ten_nganh, ma_khoi, gioi_tinh, khu_vuc, diem_chuan, chi_tieu
FROM view_tra_cuu_diem
WHERE ten_khong_dau ILIKE '%hoc vien ky thuat quan su%' AND nam = 2024
ORDER BY ten_nganh, ma_khoi, khu_vuc
LIMIT 100;""",
            },
            {
                "question": "Điểm chuẩn nữ Học viện Kỹ thuật Quân sự qua các năm?",
                "sql": """SELECT nam, ten_truong, ten_nganh, ma_khoi, gioi_tinh, khu_vuc, diem_chuan, chi_tieu
FROM view_tra_cuu_diem
WHERE ten_khong_dau ILIKE '%hoc vien ky thuat quan su%' AND gioi_tinh = 'nu'
ORDER BY nam ASC, ten_nganh, khu_vuc
LIMIT 100;""",
            },
            {
                "question": "Tôi thi được 26.5 điểm thì có đỗ Học viện Hải quân năm 2025 không?",
                "sql": """SELECT nam, ten_truong, ten_nganh, ma_khoi, gioi_tinh, khu_vuc, diem_chuan, chi_tieu
FROM view_tra_cuu_diem
WHERE ten_khong_dau ILIKE '%hoc vien hai quan%' AND nam = 2025
ORDER BY ten_nganh, ma_khoi, khu_vuc
LIMIT 100;""",
            },
            {
                "question": "Với 25 điểm khối A, tôi có thể vào trường nào năm 2024?",
                "sql": """SELECT nam, ten_truong, ten_nganh, ma_khoi, gioi_tinh, khu_vuc, diem_chuan
FROM view_tra_cuu_diem
WHERE diem_chuan <= 25 AND nam = 2024
ORDER BY diem_chuan DESC
LIMIT 50;""",
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

    def _fix_filter_values(self, sql: str, entities: dict) -> str:
        """Post-process SQL to correct filter values that LLM commonly gets wrong.

        Fixes gioi_tinh and khu_vuc filter values based on extracted entities,
        overriding whatever the LLM generated.
        """
        import re

        gioi_tinh = entities.get("gioi_tinh")
        if gioi_tinh:
            # Replace any variant the LLM might have used
            sql = re.sub(
                r"gioi_tinh\s*=\s*'[^']*'",
                f"gioi_tinh = '{gioi_tinh}'",
                sql,
                flags=re.IGNORECASE,
            )

        khu_vuc = entities.get("khu_vuc")
        if khu_vuc:
            sql = re.sub(
                r"khu_vuc\s*=\s*'[^']*'",
                f"khu_vuc = '{khu_vuc}'",
                sql,
                flags=re.IGNORECASE,
            )

        return sql

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

        # Build markdown table in Python — never rely on LLM for data formatting
        table = self._build_markdown_table(results)

        # Ask LLM only for a short analysis/intro (no raw data listing)
        score = entities.get("score")
        score_context = f"\nNgười dùng hỏi với điểm số: {score}" if score else ""

        prompt = f"""Trả lời câu hỏi dưới đây bằng 1-3 câu ngắn gọn bằng tiếng Việt.
KHÔNG liệt kê lại dữ liệu vì đã có bảng chi tiết bên dưới.
Chỉ viết nhận xét/phân tích ngắn (ví dụ: tổng kết điểm cao/thấp, so sánh khu vực, kết luận với điểm thi cụ thể...).{score_context}

Câu hỏi: {query}
Dữ liệu ({len(results)} dòng): {json.dumps(results, ensure_ascii=False)}"""

        intro = await self.llm_service.generate(
            prompt=prompt,
            system_prompt="Bạn là trợ lý tư vấn tuyển sinh quân sự. Chỉ viết phần nhận xét, không liệt kê lại bảng dữ liệu.",
        )

        return f"{intro}\n\n{table}"

    def _build_markdown_table(self, results: list[dict]) -> str:
        """Build a clean markdown table from SQL results.

        Rows sharing the same (năm, ngành, giới tính, khu vực, điểm chuẩn, chỉ tiêu)
        are merged into one row with combined khối (e.g. "A00, A01").
        năm is included in the group key so rows from different years are never merged.
        """
        GIOI_TINH_MAP = {"nam": "Nam", "nu": "Nữ"}
        KHU_VUC_MAP = {"mien_bac": "Miền Bắc", "mien_nam": "Miền Nam"}

        def _val(value, val_map=None) -> str:
            """Normalize and optionally map a cell value."""
            if value is None:
                return ""
            v = str(value).strip()
            if v == "":
                return ""
            if val_map:
                return val_map.get(v.lower(), v)
            return v

        # Group key includes `nam` và `ten_truong` so different years/schools are never collapsed
        from collections import OrderedDict
        groups: OrderedDict = OrderedDict()
        for row in results:
            group_key = (
                _val(row.get("nam")),
                _val(row.get("ten_truong")),
                _val(row.get("ten_nganh")),
                _val(row.get("gioi_tinh"), GIOI_TINH_MAP),
                _val(row.get("khu_vuc"), KHU_VUC_MAP),
                _val(row.get("diem_chuan")),
                _val(row.get("chi_tieu")),
                _val(row.get("ghi_chu")),
            )
            khoi = _val(row.get("ma_khoi"))
            if group_key not in groups:
                groups[group_key] = []
            if khoi and khoi not in groups[group_key]:
                groups[group_key].append(khoi)

        merged = []
        for (nam, ten_truong, ten_nganh, gioi_tinh, khu_vuc, diem_chuan, chi_tieu, ghi_chu), khoi_list in groups.items():
            merged.append({
                "nam": nam,
                "ten_truong": ten_truong,
                "ten_nganh": ten_nganh,
                "ma_khoi": ", ".join(sorted(khoi_list)),
                "gioi_tinh": gioi_tinh,
                "khu_vuc": khu_vuc,
                "diem_chuan": diem_chuan,
                "chi_tieu": chi_tieu,
                "ghi_chu": ghi_chu,
            })

        COLUMN_CONFIG = [
            ("nam", "Năm"),
            ("ten_truong", "Trường"),
            ("ten_nganh", "Ngành"),
            ("ma_khoi", "Khối"),
            ("gioi_tinh", "Giới tính"),
            ("khu_vuc", "Khu vực"),
            ("diem_chuan", "Điểm chuẩn"),
            ("chi_tieu", "Chỉ tiêu"),
            ("ghi_chu", "Ghi chú"),
        ]

        active_cols = [
            (key, display)
            for key, display in COLUMN_CONFIG
            if any(row.get(key) for row in merged)
        ]

        if not active_cols:
            return ""

        headers = [display for _, display in active_cols]
        header_row = "| " + " | ".join(headers) + " |"
        separator  = "| " + " | ".join("---" for _ in active_cols) + " |"

        data_rows = [
            "| " + " | ".join(row.get(key, "") for key, _ in active_cols) + " |"
            for row in merged
        ]

        return "\n".join([header_row, separator] + data_rows)


# Factory function
def get_sql_agent() -> SQLAgent:
    """Get SQL Agent instance."""
    return SQLAgent(
        max_retries=settings.sql_max_retries,
        few_shot_count=settings.sql_few_shot_examples,
    )
