"""BM25 sparse search, RRF fusion, and deduplication for hybrid RAG."""

import logging
import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from src.core.config import settings

logger = logging.getLogger(__name__)

VIETNAMESE_STOPWORDS = {
    "và", "của", "là", "có", "trong", "cho", "được", "với", "này", "đó",
    "các", "một", "những", "không", "theo", "về", "tại", "từ", "đến",
    "khi", "để", "do", "bởi", "hoặc", "hay", "cũng", "đã", "sẽ",
    "đang", "rồi", "mà", "thì", "nếu", "vì", "nên", "nhưng", "tuy",
    "dù", "song", "lại", "còn", "đều", "rất", "quá", "lắm", "hơn",
    "nhất", "bị", "ra", "vào", "lên", "xuống", "trên", "dưới", "giữa",
    "sau", "trước", "ngoài", "gì", "ai", "nào", "đâu", "sao", "thế",
    "bao", "mấy", "như", "thì", "mới", "vừa", "chỉ", "đều", "cùng",
    "hết", "luôn", "ngay", "chưa", "vẫn", "phải",
}


class BM25:
    """BM25 scoring for Vietnamese legal text."""

    def __init__(
        self,
        k1: float = None,
        b: float = None,
    ):
        self.k1 = k1 or settings.bm25_k1
        self.b = b or settings.bm25_b
        self._idf_cache: Dict[str, float] = {}
        self._doc_tokens: List[List[str]] = []
        self._avg_dl: float = 0.0
        self._doc_count: int = 0
        self._built = False

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Tokenize Vietnamese text with stopword removal.

        Args:
            text: Input text.

        Returns:
            List of tokens.
        """
        text = text.lower()
        text = re.sub(r"[^\w\sàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]", " ", text)
        tokens = text.split()
        return [t for t in tokens if t not in VIETNAMESE_STOPWORDS and len(t) > 1]

    def build_index(self, documents: List[str]):
        """Build BM25 index from document texts.

        Args:
            documents: List of document content strings.
        """
        self._doc_tokens = [self.tokenize(doc) for doc in documents]
        self._doc_count = len(documents)
        self._avg_dl = sum(len(dt) for dt in self._doc_tokens) / max(self._doc_count, 1)
        self._calculate_idf()
        self._built = True
        logger.info(f"BM25 index built: {self._doc_count} docs, avg_dl={self._avg_dl:.1f}")

    def _calculate_idf(self):
        """Calculate IDF for all terms in the corpus."""
        df = Counter()
        for doc_tokens in self._doc_tokens:
            unique_tokens = set(doc_tokens)
            for token in unique_tokens:
                df[token] += 1

        self._idf_cache = {}
        for term, freq in df.items():
            self._idf_cache[term] = math.log(
                (self._doc_count - freq + 0.5) / (freq + 0.5) + 1
            )

    def calculate_bm25_scores(self, query: str) -> List[float]:
        """Calculate BM25 scores for all documents given a query.

        Args:
            query: Search query.

        Returns:
            List of BM25 scores, one per document.
        """
        if not self._built:
            return []

        query_tokens = self.tokenize(query)
        scores = []

        for doc_tokens in self._doc_tokens:
            score = 0.0
            doc_len = len(doc_tokens)
            tf_map = Counter(doc_tokens)

            for qt in query_tokens:
                if qt not in self._idf_cache:
                    continue
                idf = self._idf_cache[qt]
                tf = tf_map.get(qt, 0)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / max(self._avg_dl, 1))
                score += idf * numerator / max(denominator, 0.001)

            scores.append(score)

        return scores


def reciprocal_rank_fusion(
    ranked_lists: List[List[Tuple[int, float]]],
    k: int = None,
) -> List[Tuple[int, float]]:
    """Reciprocal Rank Fusion to combine multiple ranked lists.

    Args:
        ranked_lists: List of ranked lists, each containing (doc_index, score) tuples.
        k: RRF constant (default from settings).

    Returns:
        Fused ranked list of (doc_index, rrf_score) tuples, sorted descending.
    """
    k = k or settings.rrf_k
    rrf_scores: Dict[int, float] = {}

    for ranked_list in ranked_lists:
        for rank, (doc_idx, _score) in enumerate(ranked_list):
            if doc_idx not in rrf_scores:
                rrf_scores[doc_idx] = 0.0
            rrf_scores[doc_idx] += 1.0 / (k + rank + 1)

    sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_results


def deduplicate_chunks(
    chunks: List[Dict],
    threshold: float = None,
) -> List[Dict]:
    """Deduplicate chunks using Jaccard similarity.

    Args:
        chunks: List of chunk dictionaries.
        threshold: Jaccard similarity threshold for dedup.

    Returns:
        Deduplicated list of chunks.
    """
    threshold = threshold or settings.dedup_threshold

    if not chunks:
        return []

    unique = [chunks[0]]

    for chunk in chunks[1:]:
        is_dup = False
        chunk_tokens = set(BM25.tokenize(chunk.get("content", "")))

        for existing in unique:
            existing_tokens = set(BM25.tokenize(existing.get("content", "")))
            if not chunk_tokens or not existing_tokens:
                continue
            intersection = chunk_tokens & existing_tokens
            union = chunk_tokens | existing_tokens
            jaccard = len(intersection) / max(len(union), 1)

            if jaccard >= threshold:
                is_dup = True
                break

        if not is_dup:
            unique.append(chunk)

    if len(chunks) != len(unique):
        logger.info(f"Dedup: {len(chunks)} -> {len(unique)} chunks (removed {len(chunks) - len(unique)})")

    return unique
