"""Advanced Hybrid Reranking with Cross-Encoder ensemble and metadata scoring."""

import logging
import re
from typing import Any, Dict, List, Optional

from src.core.config import settings
from src.agents.components.hierarchy import build_legal_hierarchy_path, find_parent_chunks

logger = logging.getLogger(__name__)

# Section type weights for metadata scoring
SECTION_TYPE_WEIGHTS = {
    "diem": 0.9,
    "dieu": 0.8,
    "khoan": 0.7,
    "muc": 0.6,
    "chuong": 0.3,
    "unknown": 0.4,
}


class HybridReranker:
    """Advanced reranker using Cross-Encoder + Retrieval Score + Metadata Score."""

    def __init__(self):
        self._model = None
        self.weights = settings.reranker_weights
        self.model_name = settings.cross_encoder_model

    @property
    def model(self):
        """Lazy load CrossEncoder."""
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                logger.info(f"Loading Cross-Encoder: {self.model_name}")
                self._model = CrossEncoder(self.model_name, max_length=512)
                logger.info("Cross-Encoder loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load CrossEncoder: {e}")
                self._model = None
        return self._model

    def _extract_target_entities(self, query: str) -> dict:
        """Trích xuất các thực thể ngữ cảnh cần khớp trong chunk.

        Dùng để boost chunk chứa quy định RIÊNG khi query hỏi về
        đối tượng cụ thể (khu vực, dân tộc), tránh LLM dùng quy định chung.

        Returns:
            Dict with 'khu_vuc' (str | None), 'dan_toc' (bool).
        """
        q = query.lower()
        entities: dict = {"khu_vuc": None, "dan_toc": False}

        # Khu vực 1 / 2 / 3
        if re.search(r"khu\s*vực\s*1|kv\s*1|hải\s*đảo", q):
            entities["khu_vuc"] = "1"
        elif re.search(r"khu\s*vực\s*2|kv\s*2", q):
            entities["khu_vuc"] = "2"
        elif re.search(r"khu\s*vực\s*3|kv\s*3", q):
            entities["khu_vuc"] = "3"

        # Dân tộc thiểu số
        if re.search(r"dân\s*tộc\s*thiểu\s*số|dtts|vùng\s*cao", q):
            entities["dan_toc"] = True

        return entities

    def _entity_match_bonus(self, query: str, content: str) -> float:
        """Bonus cho chunk chứa quy định RIÊNG khớp với đối tượng trong query.

        Ví dụ: query hỏi "khu vực 1" → Diem d (khu vực 1: 1.60m) được +0.35
        so với Diem b (quy định chung: 1.65m) → Diem d lên #1 trong reranking.

        Returns:
            Bonus score (0.0 – 0.35).
        """
        entities = self._extract_target_entities(query)
        content_lower = content.lower()
        bonus = 0.0

        if entities["khu_vuc"]:
            kv = entities["khu_vuc"]
            kv_patterns = {
                "1": r"khu\s*vực\s*1|hải\s*đảo|dân\s*tộc\s*thiểu\s*số",
                "2": r"khu\s*vực\s*2",
                "3": r"khu\s*vực\s*3",
            }
            if re.search(kv_patterns.get(kv, ""), content_lower):
                bonus = max(bonus, 0.35)

        if entities["dan_toc"] and re.search(r"dân\s*tộc\s*thiểu\s*số", content_lower):
            bonus = max(bonus, 0.30)

        return bonus

    def _extract_cited_references(self, query: str) -> dict:
        """Extract cited legal references from query (Điều, Khoản, Chương).

        Args:
            query: User query.

        Returns:
            Dict with 'article', 'clause', 'chapter' lists.
        """
        return {
            "article": re.findall(r'(?:điều|Điều)\s+(\d+)', query, re.IGNORECASE),
            "clause":  re.findall(r'(?:khoản|Khoản)\s+(\d+)', query, re.IGNORECASE),
            "chapter": re.findall(r'(?:chương|Chương)\s+([IVXLCDM]+|\d+)', query, re.IGNORECASE),
        }

    def calculate_metadata_score(self, chunk: Dict, query: str) -> float:
        """Calculate score based on document metadata and structure.

        Uses section_type weighting, title matching, content length bonus,
        and citation exact-match bonus.

        Args:
            chunk: Chunk dictionary with metadata.
            query: User query.

        Returns:
            Metadata score between 0 and 1.
        """
        metadata = chunk.get("metadata", {})
        score = 0.0

        # 1. Section type score
        section_type = self._get_section_type(chunk)
        score += SECTION_TYPE_WEIGHTS.get(section_type, 0.4) * 0.5

        # 2. Title matching with query
        query_lower = query.lower()
        query_tokens = set(query_lower.split())

        titles = [
            metadata.get("article_title", ""),
            metadata.get("chapter_title", ""),
            metadata.get("section_title", ""),
        ]

        best_overlap = 0.0
        for title in titles:
            if not title:
                continue
            title_tokens = set(title.lower().split())
            if title_tokens and query_tokens:
                overlap = len(query_tokens & title_tokens) / max(len(query_tokens), 1)
                best_overlap = max(best_overlap, overlap)

        score += best_overlap * 0.4

        # 3. Content length bonus (longer content = more informative, up to a point)
        content = chunk.get("content", "")
        content_len = len(content)
        if content_len > 200:
            score += 0.1
        elif content_len > 100:
            score += 0.05

        # 4. Citation exact-match bonus (Điều/Khoản/Chương được nhắc trực tiếp)
        cited_refs = self._extract_cited_references(query)
        if any(cited_refs.values()):
            cite_bonus = 0.0
            if str(metadata.get("article", "")) in cited_refs.get("article", []):
                cite_bonus = max(cite_bonus, 0.40)
            if str(metadata.get("chapter", "")) in cited_refs.get("chapter", []):
                cite_bonus = max(cite_bonus, 0.20)
            if str(metadata.get("clause", "")) in cited_refs.get("clause", []):
                cite_bonus += 0.15
            score += cite_bonus

        # 5. Entity match bonus (khu vực, dân tộc thiểu số)
        # Đảm bảo quy định riêng luôn xếp trên quy định chung khi query hỏi về đối tượng cụ thể
        score += self._entity_match_bonus(query, content)

        return min(score, 1.0)

    def _get_section_type(self, chunk: Dict) -> str:
        """Determine section type of a chunk."""
        metadata = chunk.get("metadata", {})
        content = chunk.get("content", "").lower()

        if metadata.get("point") or metadata.get("point_number") or re.match(r"^[a-zđ]\)", content):
            return "diem"
        if metadata.get("clause") or metadata.get("clause_number"):
            return "khoan"
        if metadata.get("article") or metadata.get("article_number"):
            return "dieu"
        if metadata.get("section") or metadata.get("section_number"):
            return "muc"
        if metadata.get("chapter") or metadata.get("chapter_number"):
            return "chuong"
        return "unknown"

    def _build_rich_text(self, chunk: Dict) -> str:
        """Build rich text for cross-encoder scoring.

        Order: legal path → title → content (main) → parent context (brief).
        Placing content before parent ensures CE attention focuses on main content.

        Args:
            chunk: Chunk dictionary.

        Returns:
            Rich text string for reranking.
        """
        parts = []

        # 1. Legal path (short, locates document)
        legal_path = build_legal_hierarchy_path(chunk)
        if legal_path:
            parts.append(legal_path)

        # 2. Title (≤100 chars)
        metadata = chunk.get("metadata", {})
        title = metadata.get("article_title") or metadata.get("section_title") or metadata.get("chapter_title", "")
        if title:
            parts.append(title[:100])

        # 3. Main content FIRST (≤400 chars) — CE attention priority
        content = chunk.get("content", "")
        parts.append(content[:400])

        # 4. Parent context LAST (≤80 chars, reduced from 150)
        try:
            parents = find_parent_chunks(chunk, max_levels=1)
            for parent in parents:
                parent_content = parent.get("content", "")
                if parent_content:
                    parts.append(parent_content[:80])
        except Exception:
            pass

        return " | ".join(parts)

    def rerank(
        self,
        query: str,
        chunks: List[Dict],
        top_k: int = None,
        use_ensemble: bool = True,
        intent: str = "general",
    ) -> List[Dict]:
        """Perform hybrid reranking with intent-adaptive weights.

        Args:
            query: User query.
            chunks: List of chunk dicts (must have 'content', 'metadata', 'score').
            top_k: Number of chunks to return.
            use_ensemble: Use ensemble scoring (CE + retrieval + metadata).
            intent: Detected query intent for adaptive weight selection.

        Returns:
            Reranked list of chunks with '_rerank_score' field.
        """
        if not chunks:
            return []

        top_k = top_k or settings.reranker_top_k

        # Select intent-adaptive weights
        weights = settings.reranker_weights_by_intent.get(intent, settings.reranker_weights)

        # Try cross-encoder scoring
        ce_scores = None
        if settings.use_cross_encoder and self.model is not None:
            try:
                pairs = [(query, self._build_rich_text(chunk)) for chunk in chunks]
                raw_scores = self.model.predict(pairs)
                # Normalize from [-10, 10] to [0, 1]
                ce_scores = [(float(s) + 10.0) / 20.0 for s in raw_scores]
                ce_scores = [max(0.0, min(1.0, s)) for s in ce_scores]
            except Exception as e:
                logger.warning(f"Cross-encoder scoring failed: {e}")
                ce_scores = None

        # Score each chunk
        scored_chunks = []
        for i, chunk in enumerate(chunks):
            retrieval_score = chunk.get("score", 0.0)
            meta_score = self.calculate_metadata_score(chunk, query)

            if ce_scores is not None and use_ensemble and settings.reranker_ensemble:
                # Ensemble with intent-adaptive weights
                final_score = (
                    weights["cross_encoder"] * ce_scores[i]
                    + weights["retrieval"] * retrieval_score
                    + weights["metadata"] * meta_score
                )
            else:
                # Fallback: Retrieval 70% + Metadata 30%
                final_score = 0.7 * retrieval_score + 0.3 * meta_score

            chunk["_rerank_score"] = final_score
            chunk["_rerank_debug"] = {
                "ce": round(ce_scores[i], 3) if ce_scores else None,
                "retrieval": round(retrieval_score, 3),
                "meta": round(meta_score, 3),
                "final": round(final_score, 3),
                "intent": intent,
            }
            scored_chunks.append(chunk)

        scored_chunks.sort(key=lambda x: x.get("_rerank_score", 0), reverse=True)

        score_strs = [f"{c.get('_rerank_score', 0):.3f}" for c in scored_chunks[:top_k]]
        logger.info(
            f"Reranked {len(chunks)} chunks -> top {top_k}, "
            f"CE={'yes' if ce_scores else 'no'}, "
            f"scores=[{', '.join(score_strs)}]"
        )

        return scored_chunks[:top_k]
