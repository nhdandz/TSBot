"""Semantic caching mechanism for RAG."""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
from src.core.config import settings

logger = logging.getLogger(__name__)


class SemanticCache:
    """In-memory semantic cache using cosine similarity."""

    def __init__(self):
        """Initialize semantic cache."""
        self._cache: List[Dict[str, Any]] = []
        self._ttl_hours = settings.cache_ttl_hours
        self._threshold = settings.cache_similarity_threshold

    def get_cache_key(self, query: str) -> str:
        """Generate MD5 hash for query."""
        return hashlib.md5(query.lower().encode()).hexdigest()

    def lookup(self, query_embedding: np.ndarray, threshold: Optional[float] = None) -> Optional[Dict]:
        """Find similar query in cache.
        
        Args:
            query_embedding: Embedding of the current query.
            threshold: Similarity threshold (overrides default).
            
        Returns:
            Cached response if hit, else None.
        """
        if not self._cache:
            return None

        effective_threshold = threshold or self._threshold
        current_time = datetime.now()
        
        # Ensure query embedding is 2D
        if query_embedding.ndim == 1:
            query_vec = query_embedding.reshape(1, -1)
        else:
            query_vec = query_embedding

        best_match = None
        max_sim = -1.0

        # Filter expired entries and find best match
        # Using list comprehension for filtering might be cleaner but we need to calc similarity
        valid_indices = []
        
        for i, entry in enumerate(self._cache):
            # Check TTL
            if (current_time - entry['timestamp']) > timedelta(hours=self._ttl_hours):
                continue
                
            valid_indices.append(i)
            
            cached_vec = entry['query_embedding']
            if cached_vec.ndim == 1:
                cached_vec = cached_vec.reshape(1, -1)
            
            # Calculate Cosine Similarity
            # Assuming embeddings are normalized (sentence-transformers usually does this)
            # If not normalized, we need: dot(a, b) / (norm(a) * norm(b))
            # Here we assume normalized for performance as per EmbeddingService
            similarity = np.dot(cached_vec, query_vec.T).item()
            
            if similarity > max_sim:
                max_sim = similarity
                best_match = entry

        # Clean up expired entries periodically or just verify on access?
        # For simple list, we can clean up if list gets too big
        if len(self._cache) > 1000:
            self.cleanup()

        if best_match and max_sim >= effective_threshold:
            logger.info(f"Cache Hit! Similarity: {max_sim:.4f}")
            return {
                "response": best_match['response'],
                "similarity": max_sim,
                "original_query": best_match['query_text']
            }
        
        return None

    def add(self, query_text: str, query_embedding: np.ndarray, response: Dict):
        """Add entry to cache.
        
        Args:
            query_text: Original query text.
            query_embedding: Query vector.
            response: Response dictionary to cache.
        """
        # Remove oldest if full
        if len(self._cache) >= 200:
            self._cache.pop(0)
            
        self._cache.append({
            "query_text": query_text,
            "query_embedding": query_embedding,
            "response": response,
            "timestamp": datetime.now()
        })

    def cleanup(self):
        """Remove expired entries."""
        current_time = datetime.now()
        self._cache = [
            entry for entry in self._cache 
            if (current_time - entry['timestamp']) <= timedelta(hours=self._ttl_hours)
        ]
