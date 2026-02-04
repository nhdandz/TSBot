"""Legal RAG Agent with Advanced RAG capabilities (CRAG + Hybrid Search + Analysis)."""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, List

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
    """Legal RAG Agent implementing Advanced RAG pattern."""

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

        # Initialize Advanced Components
        if settings.use_query_analysis:
            from src.agents.components.query_processor import QueryAnalyzer, QueryExpander
            self.analyzer = QueryAnalyzer()
            self.expander = QueryExpander()
        else:
            self.analyzer = None
            self.expander = None

        if settings.use_semantic_cache:
            from src.agents.components.cache import SemanticCache
            self.cache = SemanticCache()
        else:
            self.cache = None

        if settings.use_hybrid_search and enable_reranking:
            from src.agents.components.reranker import HybridReranker
            self.reranker_module = HybridReranker()
        else:
            self.reranker_module = None

    async def process_query(
        self,
        query: str,
        context: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Process a query using Advanced RAG pattern."""
        logger.info(f"Processing RAG query: {query}")
        
        # 0. Embed Query (Reusable)
        query_embedding = self.embedding_service.encode_query(query)

        # 1. Semantic Cache Check
        if self.cache:
            cached_result = self.cache.lookup(query_embedding)
            if cached_result:
                return cached_result['response']

        # 2. Intent Analysis
        intent = "general"
        if self.analyzer:
            analysis = self.analyzer.analyze(query)
            intent = analysis['intent']
            logger.info(f"Detected intent: {intent} (conf: {analysis['confidence']})")

        # 3. Query Expansion
        search_queries = [query]
        if self.expander:
            search_queries = self.expander.expand(query, intent)
            logger.debug(f"Expanded queries: {search_queries}")

        # 4. Smart Retrieval (Parallel)
        documents = await self._retrieve_multi(search_queries)
        logger.debug(f"Initial retrieval: {len(documents)} docs")

        # 4.5. Smart Context Enrichment (Fetch Siblings)
        if settings.use_smart_retrieval:
            documents = await self._enrich_context(documents)

        # 5. Grade relevance (CRAG)
        graded_docs = await self._grade_documents(query, documents)
        
        relevant_docs = [
            d for d in graded_docs 
            if d.relevance_grade in [RelevanceGrade.RELEVANT, RelevanceGrade.PARTIALLY_RELEVANT]
        ]
        
        # 6. Query Rewrite (Fallback if no relevant docs)
        if not relevant_docs and self.enable_query_rewrite:
            logger.info("No relevant docs, rewriting query...")
            rewritten = await self._rewrite_query(query)
            if rewritten != query:
                # Retry simplier retrieval
                documents = await self._retrieve(rewritten)
                graded_docs = await self._grade_documents(query, documents)
                relevant_docs = [
                    d for d in graded_docs 
                    if d.relevance_grade in [RelevanceGrade.RELEVANT, RelevanceGrade.PARTIALLY_RELEVANT]
                ]

        # 7. Hybrid Reranking
        if self.reranker_module and relevant_docs:
            relevant_docs = self.reranker_module.rerank(
                query, relevant_docs, top_k=self.reranker_top_k
            )
        elif self.enable_reranking and relevant_docs and not self.reranker_module:
            # Fallback to old reranker logic if Hybrid Module failed to load
            # OR simple sort by retrieval score
             relevant_docs.sort(key=lambda x: x.score, reverse=True)
             relevant_docs = relevant_docs[:self.reranker_top_k]

        # 8. Generate Answer
        if relevant_docs:
            answer = await self._generate_answer(query, relevant_docs)
            sources = self._format_sources(relevant_docs)
        else:
            answer = (
                "Xin lỗi, tôi không tìm thấy thông tin phù hợp trong văn bản quy định. "
                "Bạn có thể thử hỏi lại với từ khóa cụ thể hơn."
            )
            sources = []

        result = {
            "query": query,
            "answer": answer,
            "sources": sources,
            "intent": intent,
            "documents_retrieved": len(documents),
            "documents_relevant": len(relevant_docs),
        }

        # 9. Update Cache
        if self.cache and relevant_docs and len(answer) > 50:
            self.cache.add(query, query_embedding, result)

        return result

    async def _retrieve_multi(self, queries: list[str]) -> list[RetrievedDocument]:
        """Execute retrieval for multiple queries and deduplicate."""
        all_docs = []
        seen_content_hashes = set()
        
        # Sequential for now to avoid overloading Qdrant/Embedding
        for q in queries:
            docs = await self._retrieve(q)
            for doc in docs:
                # Deduplicate by content hash
                # (doc.metadata['id'] is not guaranteed if Qdrant auto-generated UUIDs that differ on upsert)
                # But typically RAG context is deduplicated by content
                h = hash(doc.content)
                if h not in seen_content_hashes:
                    seen_content_hashes.add(h)
                    all_docs.append(doc)
        
        return all_docs

    async def _enrich_context(self, documents: list[RetrievedDocument]) -> list[RetrievedDocument]:
        """Fetch siblings/context for top documents."""
        # Only enrich top 3 to save time
        candidates = documents[:3]
        enriched_count = 0
        seen_content_hashes = {hash(d.content) for d in documents}
        
        for doc in candidates:
            article = doc.metadata.get('article')
            if not article:
                continue
                
            # Find siblings: Same Article
            try:
                # We need to use 'filter' only search, but qdrant client usually expects a vector
                # We can use the document's own vector to find similar items (which should be siblings) 
                # constrained by the Article ID
                
                # Check if we have the vector? We don't store it in RetrievedDocument.
                # Re-embed content
                doc_vector = self.embedding_service.encode_query(doc.content).tolist()
                
                siblings = await self.qdrant.search_with_filter(
                    collection_name=settings.qdrant_legal_collection,
                    query_vector=doc_vector,
                    # sibling MUST have same article
                    must_conditions=[
                        {"key": "article", "match": {"value": article}}
                    ],
                    # If we had document_number, we should restrict to same document too
                    # But often article numbers are unique enough within a context or we assume top retrieval is correct doc
                    limit=5 
                )
                
                for sib in siblings:
                    content = sib['payload'].get('content', '')
                    h = hash(content)
                    
                    if h not in seen_content_hashes:
                        seen_content_hashes.add(h)
                        sib_doc = RetrievedDocument(
                            content=content,
                            metadata=sib['payload'],
                            score=sib['score']
                        )
                        # Mark as implicit context
                        sib_doc.metadata['is_sibling'] = True
                        documents.append(sib_doc)
                        enriched_count += 1
                        
            except Exception as e:
                logger.warning(f"Failed to enrich context: {e}")
                
        if enriched_count > 0:
            logger.debug(f"Enriched context with {enriched_count} sibling chunks")
            
        return documents

    async def _retrieve(self, query: str) -> list[RetrievedDocument]:
        """Retrieve documents from vector store."""
        query_embedding = self.embedding_service.encode_query(query)

        results = await self.qdrant.search(
            collection_name=settings.qdrant_legal_collection,
            query_vector=query_embedding.tolist(),
            limit=self.top_k,
            score_threshold=self.relevance_threshold * 0.5,
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
        """Grade document relevance using LLM."""
        graded = []

        for doc in documents:
            # If explicit sibling, maybe skip grading or assume partially relevant?
            # For now, grade everything to be safe
            try:
                prompt = GRADER_PROMPT.format(
                    question=query,
                    document=doc.content[:1000],
                )

                response = await self.llm_service.generate_with_json(
                    prompt=prompt,
                    use_grader=True,
                )

                grade_str = response.get("grade", "not_relevant")
                doc.relevance_grade = RelevanceGrade(grade_str)

            except Exception as e:
                doc.relevance_grade = RelevanceGrade.PARTIALLY_RELEVANT

            graded.append(doc)

        return graded

    async def _rewrite_query(self, query: str) -> str:
        """Rewrite query for better retrieval."""
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

    async def _generate_answer(
        self,
        query: str,
        documents: list[RetrievedDocument],
    ) -> str:
        """Generate answer from relevant documents."""
        context_parts = []
        for i, doc in enumerate(documents, 1):
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
        """Format source citations."""
        sources = []
        for doc in documents:
            source = {
                "content_preview": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                "score": round(doc.rerank_score or doc.score, 3),
            }

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
