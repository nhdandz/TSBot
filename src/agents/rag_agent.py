"""Legal RAG Agent with Advanced 10-step pipeline (Hybrid Search + RRF + Hierarchy-aware)."""

import logging
from typing import Any, Dict, List, Optional

import numpy as np

from src.core.config import settings
from src.core.embeddings import get_embedding_service
from src.core.llm import get_llm_service
from src.database.qdrant import get_qdrant_db

logger = logging.getLogger(__name__)

# Intent-adaptive RRF weights: [dense_weight, sparse_weight]
INTENT_RRF_WEIGHTS = {
    "specific":    [0.40, 0.60],  # BM25 cao hơn: exact match số Điều, tên trường
    "comparison":  [0.65, 0.35],  # Dense cao hơn: semantic similarity
    "list":        [0.50, 0.50],  # Balanced
    "explanation": [0.70, 0.30],  # Dense cao hơn: conceptual understanding
    "general":     [0.60, 0.40],  # Default (from settings)
}


# --- Answer Prompt (ported from backend_v2) ---

ANSWER_PROMPT = """Bạn là trợ lý tư vấn tuyển sinh quân sự. Trả lời DỰA TRÊN ngữ cảnh bên dưới, không dùng kiến thức ngoài.

## Ngữ cảnh:
{context}

## Câu hỏi:
{question}

## Yêu cầu:
- Trích dẫn: "Theo Điều X, Khoản Y..." — không dùng "tài liệu 1/2/3"
- Nếu có quy định riêng cho đối tượng được hỏi (khu vực, giới tính, dân tộc...) → ưu tiên quy định riêng, không dùng quy định chung
- "từ X trở lên" = ≥ X (giá trị lớn hơn X cũng đủ điều kiện)
- Không có thông tin → nói rõ và khuyên liên hệ cơ quan tuyển sinh có thẩm quyền

## Format (Markdown):
- **In đậm** con số, điều kiện, thời hạn quan trọng
- Dùng `###` chia phần nếu trả lời gồm nhiều nội dung khác nhau (phải có dòng trống trước và sau `###`)
- Dùng `-` cho danh sách; trả lời thẳng vào câu hỏi trước, trích dẫn/chi tiết sau
- Khi trích dẫn nguyên văn từ văn bản quy định, dùng blockquote: `> "nội dung trích nguyên văn..."` (dòng trống trước và sau `>`)

{intent_instruction}

## Trả lời:"""

# Intent-specific instructions
INTENT_INSTRUCTIONS = {
    "specific": "Trả lời ngắn gọn, chính xác. Trích dẫn đúng Điều/Khoản.",
    "comparison": "So sánh rõ điểm giống và khác, dùng bảng nếu phù hợp.",
    "list": "Liệt kê đầy đủ, đánh số thứ tự.",
    "explanation": "Giải thích theo thứ tự các bước.",
    "general": "Trả lời tổng quan các khía cạnh liên quan.",
}

# LLM Reranking prompt
LLM_RERANK_PROMPT = """Đánh giá mức độ liên quan của đoạn văn bản sau với câu hỏi.

Câu hỏi: {query}

Đoạn văn bản:
{content}

Cho điểm từ 0 đến 10, trong đó:
- 0-3: Không liên quan
- 4-6: Liên quan một phần
- 7-10: Rất liên quan

Trả về JSON: {{"score": <số>, "reason": "<lý do ngắn>"}}"""


class RAGAgent:
    """Legal RAG Agent implementing Advanced 10-step pipeline."""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.embedding_service = get_embedding_service()
        self.qdrant = get_qdrant_db()

        # Components
        self.analyzer = None
        self.expander = None
        self.cache = None
        self.reranker = None
        self.bm25 = None

        self._init_components()

    def _init_components(self):
        """Initialize all pipeline components."""
        # Query analysis
        if settings.use_query_analysis:
            from src.agents.components.query_processor import QueryAnalyzer, QueryExpander
            self.analyzer = QueryAnalyzer()
            self.expander = QueryExpander()

        # Semantic cache
        if settings.use_semantic_cache:
            from src.agents.components.cache import SemanticCache
            self.cache = SemanticCache()

        # Reranker
        if settings.use_hybrid_search:
            from src.agents.components.reranker import HybridReranker
            self.reranker = HybridReranker()

        # BM25
        if settings.use_hybrid_search:
            self._init_bm25()

    def _init_bm25(self):
        """Initialize BM25 index from chunk_map."""
        from src.agents.components.vector_store import get_store
        from src.agents.components.bm25 import BM25

        store = get_store()
        chunks = store.get("chunks", [])

        if chunks:
            self.bm25 = BM25()
            documents = [c.get("content", "") for c in chunks]
            self.bm25.build_index(documents)
            logger.info(f"BM25 index initialized with {len(documents)} documents")
        else:
            logger.warning("No chunks loaded, BM25 will be initialized later")

    def _ensure_bm25(self):
        """Ensure BM25 is initialized (lazy init if chunks loaded after agent creation)."""
        if self.bm25 is None and settings.use_hybrid_search:
            self._init_bm25()

    async def process_query(
        self,
        query: str,
        context: Optional[dict] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Process a query using the 10-step Advanced RAG pipeline.

        Steps:
        0. Get query embedding
        1. Semantic Cache check
        2. Query Intent Analysis -> intent + adaptive settings
        3. Query Expansion -> variations
        4. Hybrid Search (Qdrant dense + BM25 sparse + RRF)
        5. Deduplication (Jaccard)
        5.5. Sibling Enrichment
        6. Cross-Encoder Reranking
        7. Multi-chunk Smart Merging
        8. Build Context with Adaptive Settings
        9. Generate Answer
        10. Update Cache
        """
        logger.info(f"[RAG] Processing query: {query}")

        # Step 0: Get query embedding
        query_embedding = self.embedding_service.encode_query(query)
        logger.info("[RAG] Step 0: Query embedding generated")

        # Step 1: Semantic Cache check
        if self.cache:
            cached_result = self.cache.lookup(query_embedding)
            if cached_result:
                logger.info("[RAG] Step 1: CACHE HIT")
                return cached_result["response"]
        logger.info("[RAG] Step 1: Cache miss")

        # Step 2: Intent Analysis
        intent = "general"
        if self.analyzer:
            analysis = self.analyzer.analyze(query)
            intent = analysis["intent"]
            logger.info(f"[RAG] Step 2: Intent={intent} (conf={analysis['confidence']:.2f})")

        # Get adaptive context settings
        ctx_settings = settings.context_settings.get(intent, settings.context_settings["general"])

        # Step 3: Query Expansion
        search_queries = [query]
        if self.expander:
            search_queries = self.expander.expand(query, intent)
            logger.info(f"[RAG] Step 3: Expanded to {len(search_queries)} variations")

        # Step 4: Hybrid Search (Qdrant + BM25 + RRF)
        self._ensure_bm25()
        candidates = await self._hybrid_search(search_queries, query_embedding, intent=intent)
        logger.info(f"[RAG] Step 4: Hybrid search returned {len(candidates)} candidates")

        if not candidates:
            return self._empty_result(query, intent)

        # Step 5: Deduplication
        from src.agents.components.bm25 import deduplicate_chunks
        candidates = deduplicate_chunks(candidates)
        logger.info(f"[RAG] Step 5: After dedup: {len(candidates)} chunks")

        # Step 5.5: Sibling Enrichment (intent-aware)
        if settings.use_smart_retrieval:
            from src.agents.components.hierarchy import enrich_with_all_siblings
            candidates = enrich_with_all_siblings(candidates, query, query_embedding, intent=intent)
            logger.info(f"[RAG] Step 5.5: After sibling enrichment: {len(candidates)} chunks")

        # Step 5.6: Parent Promotion (chỉ cho "list" intent)
        # diem chunks → khoan cha → build_enriched_context enumerate all a/b/c/d/đ
        # KHÔNG áp dụng cho "specific" intent (tránh lẫn quy định riêng biệt)
        if intent == "list" and settings.use_smart_retrieval:
            from src.agents.components.hierarchy import promote_diem_to_parent
            candidates = promote_diem_to_parent(candidates)
            logger.info(f"[RAG] Step 5.6: After parent promotion: {len(candidates)} chunks")

        # Step 6: Reranking
        if self.reranker and len(candidates) > 1:
            reranked = self.reranker.rerank(
                query=query,
                chunks=candidates,
                top_k=settings.reranker_top_k * 2,
                use_ensemble=settings.reranker_ensemble,
                intent=intent,
            )
        else:
            # Fallback: LLM reranking or simple score sort
            reranked = await self._llm_rerank_fallback(query, candidates)
        logger.info(f"[RAG] Step 6: After reranking: {len(reranked)} chunks")

        # Step 7: Smart Merging
        from src.agents.components.hierarchy import merge_chunks_smart
        merged = merge_chunks_smart(reranked, query, query_embedding, ctx_settings)
        logger.info(f"[RAG] Step 7: After merging: {len(merged)} chunks")

        if not merged:
            return self._empty_result(query, intent)

        # Step 8: Build Context
        from src.agents.components.hierarchy import build_multi_chunk_context
        context_text = build_multi_chunk_context(merged, query, query_embedding, ctx_settings)
        logger.info(f"[RAG] Step 8: Context built ({len(context_text)} chars)")

        sources = self._format_sources(merged)

        # Stream mode: skip LLM answer generation, return context for supervisor streaming
        if stream:
            logger.info(f"[RAG] Stream mode: returning context ({len(context_text)} chars) for supervisor")
            return {
                "query": query,
                "context": context_text,
                "sources": sources,
                "intent": intent,
                "documents_retrieved": len(candidates),
                "documents_relevant": len(merged),
            }

        # Step 9: Generate Answer
        answer = await self._generate_answer(query, context_text, intent)
        logger.info(f"[RAG] Step 9: Answer generated ({len(answer)} chars)")

        result = {
            "query": query,
            "answer": answer,
            "sources": sources,
            "intent": intent,
            "documents_retrieved": len(candidates),
            "documents_relevant": len(merged),
        }

        # Step 10: Update Cache
        if self.cache and merged and len(answer) > 50:
            self.cache.add(query, query_embedding, result)
            logger.info("[RAG] Step 10: Cache updated")

        return result

    async def _hybrid_search(
        self,
        queries: List[str],
        query_embedding: np.ndarray,
        intent: str = "general",
    ) -> List[Dict]:
        """Execute hybrid search: Qdrant dense + BM25 sparse + RRF fusion.

        Args:
            queries: List of query variations.
            query_embedding: Embedding of the original query.
            intent: Detected query intent for adaptive RRF weights.

        Returns:
            Fused list of candidate chunks.
        """
        from src.agents.components.bm25 import reciprocal_rank_fusion
        from src.agents.components.vector_store import get_store

        store = get_store()
        all_chunks = store.get("chunks", [])
        top_k = settings.rag_top_k

        all_dense_results = []
        all_bm25_results = []

        for q in queries:
            # Dense search via Qdrant
            q_embedding = self.embedding_service.encode_query(q)
            qdrant_results = await self.qdrant.search(
                collection_name=settings.qdrant_legal_collection,
                query_vector=q_embedding.tolist(),
                limit=top_k * 2,
            )

            dense_ranked = []
            for r in qdrant_results:
                dense_ranked.append((r["id"], r["score"], r["payload"]))
            all_dense_results.extend(dense_ranked)

            # BM25 sparse search
            if self.bm25 and all_chunks:
                bm25_scores = self.bm25.calculate_bm25_scores(q)
                bm25_ranked = []
                for idx, score in enumerate(bm25_scores):
                    if score > 0:
                        bm25_ranked.append((idx, score))
                bm25_ranked.sort(key=lambda x: x[1], reverse=True)
                all_bm25_results.extend(bm25_ranked[:top_k * 2])

        # RRF Fusion
        if all_dense_results and all_bm25_results:
            # Convert to indexed format for RRF
            # Map Qdrant results to indices in all_chunks by matching chunk_id
            chunk_id_to_idx = {}
            for idx, chunk in enumerate(all_chunks):
                cid = chunk.get("id") or chunk.get("metadata", {}).get("chunk_id")
                if cid:
                    chunk_id_to_idx[str(cid)] = idx

            dense_for_rrf = []
            dense_score_map = {}
            for doc_id, score, payload in all_dense_results:
                idx = chunk_id_to_idx.get(str(doc_id))
                # Try matching by chunk_id in payload
                if idx is None:
                    payload_cid = payload.get("chunk_id", "")
                    idx = chunk_id_to_idx.get(str(payload_cid))
                if idx is not None:
                    dense_for_rrf.append((idx, score))
                    dense_score_map[idx] = max(dense_score_map.get(idx, 0), score)

            bm25_for_rrf = all_bm25_results

            rrf_weights = INTENT_RRF_WEIGHTS.get(intent, INTENT_RRF_WEIGHTS["general"])
            fused = reciprocal_rank_fusion([dense_for_rrf, bm25_for_rrf], weights=rrf_weights)

            # Convert back to chunks
            candidates = []
            seen = set()
            for doc_idx, rrf_score in fused[:top_k * 3]:
                if doc_idx in seen or doc_idx >= len(all_chunks):
                    continue
                seen.add(doc_idx)
                chunk = dict(all_chunks[doc_idx])
                chunk["score"] = dense_score_map.get(doc_idx, rrf_score)
                chunk["_rrf_score"] = rrf_score
                candidates.append(chunk)

            return candidates

        elif all_dense_results:
            # Dense only
            candidates = []
            seen = set()
            for doc_id, score, payload in all_dense_results:
                content = payload.get("content", "")
                content_hash = hash(content)
                if content_hash in seen:
                    continue
                seen.add(content_hash)
                chunk = {
                    "id": doc_id,
                    "content": content,
                    "metadata": payload,
                    "score": score,
                }
                candidates.append(chunk)

            candidates.sort(key=lambda x: x["score"], reverse=True)
            return candidates[:top_k * 3]

        return []

    async def _llm_rerank_fallback(
        self,
        query: str,
        chunks: List[Dict],
    ) -> List[Dict]:
        """LLM-based reranking fallback when Cross-Encoder is unavailable.

        Args:
            query: User query.
            chunks: Candidate chunks.

        Returns:
            Reranked chunks.
        """
        top_k = settings.reranker_top_k

        # Simple: try LLM scoring for top candidates
        scored = []
        for chunk in chunks[:top_k * 2]:
            content = chunk.get("content", "")
            try:
                prompt = LLM_RERANK_PROMPT.format(query=query, content=content[:500])
                response = await self.llm_service.generate_with_json(
                    prompt=prompt,
                    use_grader=True,
                )
                llm_score = float(response.get("score", 5)) / 10.0
                chunk["_rerank_score"] = llm_score * 0.6 + chunk.get("score", 0) * 0.4
            except Exception:
                chunk["_rerank_score"] = chunk.get("score", 0)
            scored.append(chunk)

        scored.sort(key=lambda x: x.get("_rerank_score", 0), reverse=True)
        return scored[:top_k]

    async def _generate_answer(
        self,
        query: str,
        context: str,
        intent: str,
    ) -> str:
        """Generate answer using LLM with intent-adaptive prompt.

        Args:
            query: User query.
            context: Enriched context string.
            intent: Detected intent.

        Returns:
            Generated answer text.
        """
        intent_instruction = INTENT_INSTRUCTIONS.get(intent, INTENT_INSTRUCTIONS["general"])

        prompt = ANSWER_PROMPT.format(
            context=context,
            question=query,
            intent_instruction=intent_instruction,
        )

        logger.debug(f"[RAG] Prompt length: {len(prompt)} chars")
        answer = await self.llm_service.generate(prompt=prompt)
        return answer

    def _format_sources(self, chunks: List[Dict]) -> List[Dict]:
        """Format source citations from chunks.

        Args:
            chunks: List of chunk dictionaries.

        Returns:
            List of source citation dictionaries.
        """
        sources = []
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            content = chunk.get("content", "")

            source = {
                "content_preview": content[:200] + "..." if len(content) > 200 else content,
                "content": content,
                "score": round(chunk.get("score", 0), 3),
            }

            from src.agents.components.hierarchy import build_legal_hierarchy_path
            legal_path = build_legal_hierarchy_path(chunk)
            if legal_path:
                source["legal_path"] = legal_path

            if metadata.get("chapter"):
                source["chapter"] = metadata["chapter"]
            if metadata.get("article"):
                source["article"] = metadata["article"]
            if metadata.get("source"):
                source["document"] = metadata["source"]

            sources.append(source)

        return sources

    def _empty_result(self, query: str, intent: str) -> Dict[str, Any]:
        """Return empty result when no relevant documents found."""
        logger.warning("[RAG] No relevant documents found")
        return {
            "query": query,
            "answer": (
                "Xin lỗi, tôi không tìm thấy thông tin phù hợp trong văn bản quy định. "
                "Bạn có thể thử hỏi lại với từ khóa cụ thể hơn."
            ),
            "sources": [],
            "intent": intent,
            "documents_retrieved": 0,
            "documents_relevant": 0,
        }


# Factory function
def get_rag_agent() -> RAGAgent:
    """Get RAG Agent instance."""
    return RAGAgent()
