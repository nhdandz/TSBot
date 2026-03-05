"""Semantic caching mechanism for RAG — hybrid RAM + Redis backend."""

import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np

from src.core.config import settings

logger = logging.getLogger(__name__)


class SemanticCache:
    """Hybrid semantic cache: exact hash lookup via Redis + cosine similarity in RAM."""

    def __init__(self):
        self._cache: List[Dict[str, Any]] = []
        self._ttl_hours = settings.cache_ttl_hours
        self._threshold = settings.cache_similarity_threshold
        self._redis: Optional[Any] = None  # redis.asyncio.Redis, lazy init
        self._redis_initialized = False

    # ── Helpers ────────────────────────────────────────────────────────────

    def get_cache_key(self, query: str) -> str:
        """Generate MD5 hash key cho Redis."""
        return f"tsbot:cache:{hashlib.md5(query.lower().strip().encode()).hexdigest()}"

    async def _get_redis(self) -> Optional[Any]:
        """Lazy init Redis connection."""
        if self._redis_initialized:
            return self._redis
        self._redis_initialized = True

        if not getattr(settings, "use_redis_cache", False):
            return None

        redis_url = getattr(settings, "redis_url", None)
        if not redis_url:
            return None

        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            await self._redis.ping()
            logger.info("Redis cache connected")
        except Exception as e:
            logger.warning(f"Redis cache unavailable: {e}")
            self._redis = None

        return self._redis

    async def preload_from_redis(self):
        """Preload valid cache entries từ Redis vào RAM khi startup."""
        r = await self._get_redis()
        if not r:
            return

        try:
            keys = await r.keys("tsbot:cache:*")
            loaded = 0
            current_time = datetime.now(timezone.utc)

            for key in keys:
                raw = await r.get(key)
                if not raw:
                    continue
                try:
                    entry = json.loads(raw)
                except Exception:
                    continue

                # Parse timestamp
                ts_str = entry.get("timestamp")
                try:
                    ts = datetime.fromisoformat(ts_str)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                except Exception:
                    continue

                if (current_time - ts) > timedelta(hours=self._ttl_hours):
                    continue

                # Reconstruct embedding từ list
                emb_list = entry.get("query_embedding")
                if not emb_list:
                    continue
                query_embedding = np.array(emb_list, dtype=np.float32)

                self._cache.append({
                    "query_text": entry["query_text"],
                    "query_embedding": query_embedding,
                    "response": entry["response"],
                    "timestamp": ts,
                })
                loaded += 1

            logger.info(f"Preloaded {loaded}/{len(keys)} entries from Redis into RAM cache")
        except Exception as e:
            logger.warning(f"Redis preload failed: {e}")

    # ── Sync lookup (kept for backward compat in rag_agent) ────────────────

    def lookup(self, query_embedding: np.ndarray, threshold: Optional[float] = None) -> Optional[Dict]:
        """Cosine similarity lookup trong RAM (sync)."""
        if not self._cache:
            return None

        effective_threshold = threshold or self._threshold
        current_time = datetime.now(timezone.utc)

        if query_embedding.ndim == 1:
            query_vec = query_embedding.reshape(1, -1)
        else:
            query_vec = query_embedding

        best_match = None
        max_sim = -1.0

        for entry in self._cache:
            if (current_time - entry["timestamp"]) > timedelta(hours=self._ttl_hours):
                continue

            cached_vec = entry["query_embedding"]
            if cached_vec.ndim == 1:
                cached_vec = cached_vec.reshape(1, -1)

            similarity = np.dot(cached_vec, query_vec.T).item()
            if similarity > max_sim:
                max_sim = similarity
                best_match = entry

        if len(self._cache) > 1000:
            self.cleanup()

        if best_match and max_sim >= effective_threshold:
            logger.info(f"Cache Hit (RAM cosine)! Similarity: {max_sim:.4f}")
            return {
                "response": best_match["response"],
                "similarity": max_sim,
                "original_query": best_match["query_text"],
            }

        return None

    def add(self, query_text: str, query_embedding: np.ndarray, response: Dict):
        """Add vào RAM cache (sync)."""
        if len(self._cache) >= 200:
            self._cache.pop(0)

        self._cache.append({
            "query_text": query_text,
            "query_embedding": query_embedding,
            "response": response,
            "timestamp": datetime.now(timezone.utc),
        })

    # ── Async lookup/add (dùng trong process_stream) ───────────────────────

    async def lookup_async(
        self,
        query_text: str,
        query_embedding: np.ndarray,
        threshold: Optional[float] = None,
    ) -> Optional[Dict]:
        """Async lookup: exact hash (Redis) → cosine similarity (RAM)."""
        # 1. Exact hash lookup via Redis (O(1))
        r = await self._get_redis()
        if r:
            try:
                key = self.get_cache_key(query_text)
                raw = await r.get(key)
                if raw:
                    entry = json.loads(raw)
                    ts_str = entry.get("timestamp")
                    ts = datetime.fromisoformat(ts_str)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    if (datetime.now(timezone.utc) - ts) <= timedelta(hours=self._ttl_hours):
                        logger.info("Cache Hit (Redis exact)!")
                        return {
                            "response": entry["response"],
                            "similarity": 1.0,
                            "original_query": entry["query_text"],
                        }
            except Exception as e:
                logger.debug(f"Redis lookup error: {e}")

        # 2. Cosine similarity in RAM
        return self.lookup(query_embedding, threshold)

    async def add_async(
        self,
        query_text: str,
        query_embedding: np.ndarray,
        response: Dict,
    ):
        """Async add: lưu vào RAM + Redis."""
        # Save to RAM
        self.add(query_text, query_embedding, response)

        # Save to Redis
        r = await self._get_redis()
        if r:
            try:
                key = self.get_cache_key(query_text)
                payload = {
                    "query_text": query_text,
                    "query_embedding": query_embedding.tolist(),
                    "response": response,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                ttl_seconds = int(self._ttl_hours * 3600)
                await r.setex(key, ttl_seconds, json.dumps(payload, ensure_ascii=False))
            except Exception as e:
                logger.debug(f"Redis add error: {e}")

    # ── Cleanup ────────────────────────────────────────────────────────────

    def cleanup(self):
        """Remove expired entries from RAM."""
        current_time = datetime.now(timezone.utc)
        self._cache = [
            entry for entry in self._cache
            if (current_time - entry["timestamp"]) <= timedelta(hours=self._ttl_hours)
        ]
