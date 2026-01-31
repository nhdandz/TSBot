"""Qdrant vector database client wrapper."""

import logging
from typing import Any, Optional

from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client.http import models as qmodels

from src.core.config import settings

logger = logging.getLogger(__name__)


class QdrantDB:
    """Qdrant vector database manager."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        grpc_port: Optional[int] = None,
    ):
        """Initialize Qdrant client.

        Args:
            host: Qdrant server host.
            port: Qdrant REST port.
            grpc_port: Qdrant gRPC port.
        """
        self.host = host or settings.qdrant_host
        self.port = port or settings.qdrant_port
        self.grpc_port = grpc_port or settings.qdrant_grpc_port
        self._client: Optional[QdrantClient] = None
        self._async_client: Optional[AsyncQdrantClient] = None

    @property
    def client(self) -> QdrantClient:
        """Get synchronous Qdrant client."""
        if self._client is None:
            self._client = QdrantClient(
                host=self.host,
                port=self.port,
                prefer_grpc=False,  # Use HTTP instead of gRPC
                check_compatibility=False,
            )
        return self._client

    @property
    def async_client(self) -> AsyncQdrantClient:
        """Get asynchronous Qdrant client."""
        if self._async_client is None:
            self._async_client = AsyncQdrantClient(
                host=self.host,
                port=self.port,
                prefer_grpc=False,  # Use HTTP instead of gRPC to avoid version mismatch issues
                check_compatibility=False,
            )
        return self._async_client

    async def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: str = "Cosine",
        on_disk: bool = False,
    ) -> bool:
        """Create a new collection if it doesn't exist.

        Args:
            collection_name: Name of the collection.
            vector_size: Dimension of vectors.
            distance: Distance metric (Cosine, Euclid, Dot).
            on_disk: Store vectors on disk instead of RAM.

        Returns:
            True if created, False if already exists.
        """
        try:
            collections = await self.async_client.get_collections()
            existing = [c.name for c in collections.collections]

            if collection_name in existing:
                logger.info(f"Collection '{collection_name}' already exists")
                return False

            distance_map = {
                "Cosine": qmodels.Distance.COSINE,
                "Euclid": qmodels.Distance.EUCLID,
                "Dot": qmodels.Distance.DOT,
            }

            await self.async_client.create_collection(
                collection_name=collection_name,
                vectors_config=qmodels.VectorParams(
                    size=vector_size,
                    distance=distance_map.get(distance, qmodels.Distance.COSINE),
                    on_disk=on_disk,
                ),
                optimizers_config=qmodels.OptimizersConfigDiff(
                    indexing_threshold=20000,
                ),
            )
            logger.info(f"Collection '{collection_name}' created successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise

    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection.

        Args:
            collection_name: Name of the collection.

        Returns:
            True if deleted.
        """
        try:
            await self.async_client.delete_collection(collection_name)
            logger.info(f"Collection '{collection_name}' deleted")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            raise

    async def upsert_vectors(
        self,
        collection_name: str,
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
        ids: Optional[list[str | int]] = None,
    ) -> None:
        """Insert or update vectors in collection.

        Args:
            collection_name: Target collection.
            vectors: List of embedding vectors.
            payloads: List of metadata payloads.
            ids: Optional list of IDs (auto-generated if not provided).
        """
        if ids is None:
            # Generate UUIDs
            import uuid

            ids = [str(uuid.uuid4()) for _ in vectors]

        points = [
            qmodels.PointStruct(id=id_, vector=vector, payload=payload)
            for id_, vector, payload in zip(ids, vectors, payloads)
        ]

        await self.async_client.upsert(
            collection_name=collection_name,
            points=points,
            wait=True,
        )
        logger.debug(f"Upserted {len(points)} vectors to '{collection_name}'")

    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 5,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[dict] = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors.

        Args:
            collection_name: Collection to search.
            query_vector: Query embedding vector.
            limit: Maximum number of results.
            score_threshold: Minimum similarity score.
            filter_conditions: Qdrant filter conditions.

        Returns:
            List of search results with payload and score.
        """
        query_filter = None
        if filter_conditions:
            query_filter = qmodels.Filter(**filter_conditions)

        results = await self.async_client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter,
        )

        return [
            {
                "id": str(point.id),
                "score": point.score,
                "payload": point.payload,
            }
            for point in results.points
        ]

    async def search_with_filter(
        self,
        collection_name: str,
        query_vector: list[float],
        must_conditions: Optional[list[dict]] = None,
        should_conditions: Optional[list[dict]] = None,
        must_not_conditions: Optional[list[dict]] = None,
        limit: int = 5,
        score_threshold: Optional[float] = None,
    ) -> list[dict[str, Any]]:
        """Search with advanced filtering.

        Args:
            collection_name: Collection to search.
            query_vector: Query embedding vector.
            must_conditions: All conditions must match.
            should_conditions: At least one should match.
            must_not_conditions: None should match.
            limit: Maximum results.
            score_threshold: Minimum score.

        Returns:
            Search results.
        """
        filter_clauses = {}
        if must_conditions:
            filter_clauses["must"] = [
                qmodels.FieldCondition(**cond) for cond in must_conditions
            ]
        if should_conditions:
            filter_clauses["should"] = [
                qmodels.FieldCondition(**cond) for cond in should_conditions
            ]
        if must_not_conditions:
            filter_clauses["must_not"] = [
                qmodels.FieldCondition(**cond) for cond in must_not_conditions
            ]

        query_filter = qmodels.Filter(**filter_clauses) if filter_clauses else None

        results = await self.async_client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter,
        )

        return [
            {
                "id": str(point.id),
                "score": point.score,
                "payload": point.payload,
            }
            for point in results.points
        ]

    async def get_collection_info(self, collection_name: str) -> dict[str, Any]:
        """Get collection information.

        Args:
            collection_name: Collection name.

        Returns:
            Collection info dictionary.
        """
        info = await self.async_client.get_collection(collection_name)
        return {
            "name": collection_name,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": info.status,
            "config": {
                "vector_size": info.config.params.vectors.size,
                "distance": str(info.config.params.vectors.distance),
            },
        }

    async def count_points(self, collection_name: str) -> int:
        """Count points in collection.

        Args:
            collection_name: Collection name.

        Returns:
            Number of points.
        """
        info = await self.async_client.get_collection(collection_name)
        return info.points_count or 0

    async def delete_points(
        self,
        collection_name: str,
        point_ids: Optional[list[str | int]] = None,
        filter_conditions: Optional[dict] = None,
    ) -> None:
        """Delete points from collection.

        Args:
            collection_name: Collection name.
            point_ids: Specific IDs to delete.
            filter_conditions: Delete by filter.
        """
        if point_ids:
            await self.async_client.delete(
                collection_name=collection_name,
                points_selector=qmodels.PointIdsList(points=point_ids),
            )
        elif filter_conditions:
            await self.async_client.delete(
                collection_name=collection_name,
                points_selector=qmodels.FilterSelector(
                    filter=qmodels.Filter(**filter_conditions)
                ),
            )

    async def health_check(self) -> bool:
        """Check Qdrant connectivity.

        Returns:
            True if connected.
        """
        try:
            await self.async_client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

    async def close(self) -> None:
        """Close Qdrant connections."""
        if self._async_client:
            await self._async_client.close()
            self._async_client = None
        if self._client:
            self._client.close()
            self._client = None
        logger.info("Qdrant connections closed")


# Global instance
_qdrant_instance: Optional[QdrantDB] = None


def get_qdrant_db() -> QdrantDB:
    """Get global Qdrant database instance.

    Returns:
        QdrantDB instance.
    """
    global _qdrant_instance
    if _qdrant_instance is None:
        _qdrant_instance = QdrantDB()
    return _qdrant_instance
