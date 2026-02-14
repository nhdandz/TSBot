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

    def calculate_metadata_score(self, chunk: Dict, query: str) -> float:
        """Calculate score based on document metadata and structure.

        Uses section_type weighting, title matching, and content length bonus.

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

        Includes parent context + title + legal path + truncated content.

        Args:
            chunk: Chunk dictionary.

        Returns:
            Rich text string for reranking.
        """
        parts = []

        # Parent context
        try:
            parents = find_parent_chunks(chunk, max_levels=1)
            for parent in parents:
                parent_content = parent.get("content", "")
                if parent_content:
                    parts.append(parent_content[:150])
        except Exception:
            pass

        # Legal path
        legal_path = build_legal_hierarchy_path(chunk)
        if legal_path:
            parts.append(legal_path)

        # Title
        metadata = chunk.get("metadata", {})
        title = metadata.get("article_title") or metadata.get("section_title") or metadata.get("chapter_title", "")
        if title:
            parts.append(title)

        # Content (truncated)
        content = chunk.get("content", "")
        parts.append(content[:600])

        return " | ".join(parts)

    def rerank(
        self,
        query: str,
        chunks: List[Dict],
        top_k: int = None,
        use_ensemble: bool = True,
    ) -> List[Dict]:
        """Perform hybrid reranking.

        Args:
            query: User query.
            chunks: List of chunk dicts (must have 'content', 'metadata', 'score').
            top_k: Number of chunks to return.
            use_ensemble: Use ensemble scoring (CE + retrieval + metadata).

        Returns:
            Reranked list of chunks with '_rerank_score' field.
        """
        if not chunks:
            return []

        top_k = top_k or settings.reranker_top_k

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
                # Ensemble: CE 55% + Retrieval 35% + Metadata 10%
                final_score = (
                    self.weights["cross_encoder"] * ce_scores[i]
                    + self.weights["retrieval"] * retrieval_score
                    + self.weights["metadata"] * meta_score
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
