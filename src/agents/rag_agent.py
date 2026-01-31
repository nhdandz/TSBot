"""Legal RAG Agent with Corrective RAG (CRAG) pattern."""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from src.core.config import settings
from src.core.embeddings import get_embedding_service
from src.core.llm import get_llm_service
from src.database.qdrant import get_qdrant_db

logger = logging.getLogger(__name__)


class RelevanceGrade(str, Enum):
    """Document relevance grades."""

    RELEVANT = "relevant"
    PARTIALLY_RELEVANT = "partially_relevant"
    NOT_RELEVANT = "not_relevant"


@dataclass
class RetrievedDocument:
    """A retrieved document with metadata."""

    content: str
    metadata: dict
    score: float
    relevance_grade: Optional[RelevanceGrade] = None
    rerank_score: Optional[float] = None


# Prompts
GRADER_PROMPT = """Bạn là người đánh giá mức độ liên quan của tài liệu đối với câu hỏi của người dùng.

Câu hỏi: {question}

Tài liệu:
{document}

Đánh giá tài liệu này có liên quan đến câu hỏi không:
- "relevant": Tài liệu trực tiếp trả lời hoặc cung cấp thông tin cần thiết
- "partially_relevant": Tài liệu có liên quan nhưng không trực tiếp trả lời
- "not_relevant": Tài liệu không liên quan

Trả về JSON: {{"grade": "relevant/partially_relevant/not_relevant", "reason": "lý do ngắn gọn"}}"""


REWRITE_PROMPT = """Viết lại câu hỏi sau để tìm kiếm tốt hơn trong cơ sở dữ liệu văn bản pháp quy tuyển sinh quân sự.

Câu hỏi gốc: {question}

Các từ khóa quan trọng cần giữ lại:
- Tên trường/học viện
- Tiêu chuẩn (sức khỏe, chính trị, học lực...)
- Quy trình/thủ tục
- Điều kiện/yêu cầu

Câu hỏi viết lại (chỉ trả về câu hỏi mới, không giải thích):"""


ANSWER_PROMPT = """Bạn là trợ lý tư vấn tuyển sinh quân sự Việt Nam. Dựa trên các văn bản quy định sau đây, hãy trả lời câu hỏi của người dùng.

## Văn bản quy định:
{context}

## Câu hỏi:
{question}

## Hướng dẫn trả lời:
1. Chỉ sử dụng thông tin từ văn bản được cung cấp
2. Trích dẫn điều/khoản cụ thể khi có thể
3. Nếu không tìm thấy thông tin, nói rõ là không có trong văn bản
4. Trả lời bằng tiếng Việt, rõ ràng và dễ hiểu
5. Nếu có nhiều điều kiện/yêu cầu, liệt kê theo danh sách

## Trả lời:"""


class RAGAgent:
    """Legal RAG Agent implementing Corrective RAG pattern."""

    def __init__(
        self,
        top_k: int = 5,
        relevance_threshold: float = 0.7,
        reranker_top_k: int = 3,
        enable_reranking: bool = True,
        enable_query_rewrite: bool = True,
    ):
        """Initialize RAG Agent.

        Args:
            top_k: Number of documents to retrieve.
            relevance_threshold: Minimum relevance score.
            reranker_top_k: Number of documents after reranking.
            enable_reranking: Whether to use reranker.
            enable_query_rewrite: Whether to rewrite queries.
        """
        self.top_k = top_k
        self.relevance_threshold = relevance_threshold
        self.reranker_top_k = reranker_top_k
        self.enable_reranking = enable_reranking
        self.enable_query_rewrite = enable_query_rewrite

        self.llm_service = get_llm_service()
        self.embedding_service = get_embedding_service()
        self.qdrant = get_qdrant_db()

        self._reranker = None

    @property
    def reranker(self):
        """Lazy load reranker model."""
        if self._reranker is None and self.enable_reranking:
            try:
                from sentence_transformers import CrossEncoder

                self._reranker = CrossEncoder(
                    settings.reranker_model,
                    max_length=512,
                )
                logger.info(f"Loaded reranker: {settings.reranker_model}")
            except Exception as e:
                logger.warning(f"Failed to load reranker: {e}")
                self.enable_reranking = False
        return self._reranker

    async def process_query(
        self,
        query: str,
        context: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Process a query using CRAG pattern.

        CRAG Flow:
        1. Retrieve documents
        2. Grade document relevance
        3. If low relevance, rewrite query and retry
        4. Rerank documents
        5. Generate answer

        Args:
            query: User's question.
            context: Optional conversation context.

        Returns:
            Response dictionary with answer and metadata.
        """
        logger.info(f"Processing RAG query: {query}")

        # Step 1: Initial retrieval
        documents = await self._retrieve(query)
        logger.debug(f"Retrieved {len(documents)} documents")

        # Step 2: Grade relevance
        graded_docs = await self._grade_documents(query, documents)

        # Count relevant documents
        relevant_count = sum(
            1 for d in graded_docs if d.relevance_grade == RelevanceGrade.RELEVANT
        )
        partially_count = sum(
            1 for d in graded_docs if d.relevance_grade == RelevanceGrade.PARTIALLY_RELEVANT
        )

        # Step 3: Query rewriting if needed
        if relevant_count == 0 and self.enable_query_rewrite:
            logger.info("No relevant documents, attempting query rewrite")
            rewritten_query = await self._rewrite_query(query)

            if rewritten_query != query:
                logger.debug(f"Rewritten query: {rewritten_query}")
                # Retry retrieval with rewritten query
                documents = await self._retrieve(rewritten_query)
                graded_docs = await self._grade_documents(query, documents)

        # Filter to relevant/partially relevant
        filtered_docs = [
            d for d in graded_docs
            if d.relevance_grade in [RelevanceGrade.RELEVANT, RelevanceGrade.PARTIALLY_RELEVANT]
        ]

        # Step 4: Rerank if enabled
        if self.enable_reranking and len(filtered_docs) > self.reranker_top_k:
            filtered_docs = await self._rerank(query, filtered_docs)

        # Step 5: Generate answer
        if filtered_docs:
            answer = await self._generate_answer(query, filtered_docs)
            sources = self._format_sources(filtered_docs)
        else:
            answer = (
                "Xin lỗi, tôi không tìm thấy thông tin liên quan trong văn bản quy định. "
                "Vui lòng thử hỏi cách khác hoặc liên hệ trực tiếp với cơ quan tuyển sinh."
            )
            sources = []

        return {
            "query": query,
            "answer": answer,
            "sources": sources,
            "documents_retrieved": len(documents),
            "documents_relevant": len(filtered_docs),
            "reranking_used": self.enable_reranking and len(filtered_docs) > 0,
        }

    async def _retrieve(self, query: str) -> list[RetrievedDocument]:
        """Retrieve documents from vector store.

        Args:
            query: Search query.

        Returns:
            List of retrieved documents.
        """
        # Embed query
        query_embedding = self.embedding_service.encode_query(query)

        # Search in Qdrant
        results = await self.qdrant.search(
            collection_name=settings.qdrant_legal_collection,
            query_vector=query_embedding.tolist(),
            limit=self.top_k,
            score_threshold=self.relevance_threshold * 0.5,  # Lower threshold for initial retrieval
        )

        documents = []
        for result in results:
            payload = result.get("payload", {})
            documents.append(
                RetrievedDocument(
                    content=payload.get("content", ""),
                    metadata=payload,
                    score=result.get("score", 0),
                )
            )

        return documents

    async def _grade_documents(
        self,
        query: str,
        documents: list[RetrievedDocument],
    ) -> list[RetrievedDocument]:
        """Grade document relevance using LLM.

        Args:
            query: User query.
            documents: Retrieved documents.

        Returns:
            Documents with relevance grades.
        """
        graded = []

        for doc in documents:
            try:
                prompt = GRADER_PROMPT.format(
                    question=query,
                    document=doc.content[:1000],  # Truncate for efficiency
                )

                response = await self.llm_service.generate_with_json(
                    prompt=prompt,
                    use_grader=True,  # Use smaller/faster model
                )

                grade_str = response.get("grade", "not_relevant")
                doc.relevance_grade = RelevanceGrade(grade_str)

            except Exception as e:
                logger.warning(f"Grading failed: {e}")
                # Default to partially relevant if grading fails
                doc.relevance_grade = RelevanceGrade.PARTIALLY_RELEVANT

            graded.append(doc)

        return graded

    async def _rewrite_query(self, query: str) -> str:
        """Rewrite query for better retrieval.

        Args:
            query: Original query.

        Returns:
            Rewritten query.
        """
        try:
            prompt = REWRITE_PROMPT.format(question=query)
            rewritten = await self.llm_service.generate(
                prompt=prompt,
                use_grader=True,
            )
            return rewritten.strip()
        except Exception as e:
            logger.warning(f"Query rewrite failed: {e}")
            return query

    async def _rerank(
        self,
        query: str,
        documents: list[RetrievedDocument],
    ) -> list[RetrievedDocument]:
        """Rerank documents using cross-encoder.

        Args:
            query: User query.
            documents: Documents to rerank.

        Returns:
            Reranked documents.
        """
        if not self.reranker or not documents:
            return documents[:self.reranker_top_k]

        try:
            # Prepare pairs for reranking
            pairs = [(query, doc.content) for doc in documents]

            # Get reranker scores
            scores = self.reranker.predict(pairs)

            # Update scores and sort
            for doc, score in zip(documents, scores):
                doc.rerank_score = float(score)

            # Sort by rerank score
            documents.sort(key=lambda d: d.rerank_score or 0, reverse=True)

            return documents[:self.reranker_top_k]

        except Exception as e:
            logger.warning(f"Reranking failed: {e}")
            return documents[:self.reranker_top_k]

    async def _generate_answer(
        self,
        query: str,
        documents: list[RetrievedDocument],
    ) -> str:
        """Generate answer from relevant documents.

        Args:
            query: User query.
            documents: Relevant documents.

        Returns:
            Generated answer.
        """
        # Build context from documents
        context_parts = []
        for i, doc in enumerate(documents, 1):
            # Include hierarchy path if available
            hierarchy = ""
            if doc.metadata.get("article"):
                hierarchy = f"Điều {doc.metadata['article']}"
                if doc.metadata.get("clause"):
                    hierarchy += f", Khoản {doc.metadata['clause']}"
                hierarchy = f"[{hierarchy}] "

            source = doc.metadata.get("source", "")
            if source:
                source = f"(Nguồn: {source})"

            context_parts.append(f"{i}. {hierarchy}{doc.content}\n{source}")

        context = "\n\n".join(context_parts)

        prompt = ANSWER_PROMPT.format(
            context=context,
            question=query,
        )

        answer = await self.llm_service.generate(prompt=prompt)
        return answer

    def _format_sources(
        self,
        documents: list[RetrievedDocument],
    ) -> list[dict]:
        """Format source citations.

        Args:
            documents: Source documents.

        Returns:
            List of source citations.
        """
        sources = []
        for doc in documents:
            source = {
                "content_preview": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                "score": round(doc.rerank_score or doc.score, 3),
            }

            # Add hierarchy info
            if doc.metadata.get("chapter"):
                source["chapter"] = doc.metadata["chapter"]
            if doc.metadata.get("article"):
                source["article"] = doc.metadata["article"]
            if doc.metadata.get("source"):
                source["document"] = doc.metadata["source"]

            sources.append(source)

        return sources


# Factory function
def get_rag_agent() -> RAGAgent:
    """Get RAG Agent instance."""
    return RAGAgent(
        top_k=settings.rag_top_k,
        relevance_threshold=settings.rag_relevance_threshold,
        reranker_top_k=settings.reranker_top_k,
    )
