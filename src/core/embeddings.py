"""Embedding service using Ollama for TSBot."""

import logging
from typing import Optional

import httpx
import numpy as np

from src.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Embedding service using Ollama API."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        ollama_base_url: Optional[str] = None,
    ):
        """Initialize embedding service.

        Args:
            model_name: Ollama embedding model name.
            ollama_base_url: Ollama API base URL.
        """
        self.model_name = model_name or settings.embedding_model
        self.ollama_base_url = ollama_base_url or settings.ollama_base_url
        self._dimension: Optional[int] = None

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        if self._dimension is None:
            test_embedding = self.encode("test")
            self._dimension = test_embedding.shape[-1]
        return self._dimension

    def _call_ollama_embed(self, texts: list[str]) -> list[list[float]]:
        """Call Ollama embed API synchronously.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        url = f"{self.ollama_base_url}/api/embed"
        payload = {
            "model": self.model_name,
            "input": texts,
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["embeddings"]

    async def _async_call_ollama_embed(self, texts: list[str]) -> list[list[float]]:
        """Call Ollama embed API asynchronously.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        url = f"{self.ollama_base_url}/api/embed"
        payload = {
            "model": self.model_name,
            "input": texts,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["embeddings"]

    def encode(
        self,
        texts: str | list[str],
        normalize: bool = True,
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> np.ndarray:
        """Encode texts to embeddings.

        Args:
            texts: Single text or list of texts.
            normalize: Normalize embeddings to unit length.
            batch_size: Batch size for encoding.
            show_progress: Show progress bar (unused, kept for compatibility).

        Returns:
            Numpy array of embeddings.
        """
        if isinstance(texts, str):
            texts = [texts]

        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embeddings = self._call_ollama_embed(batch)
            all_embeddings.extend(embeddings)

        result = np.array(all_embeddings, dtype=np.float32)

        if normalize:
            norms = np.linalg.norm(result, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            result = result / norms

        return result

    async def aencode(
        self,
        texts: str | list[str],
        normalize: bool = True,
        batch_size: int = 32,
    ) -> np.ndarray:
        """Async encode texts to embeddings.

        Args:
            texts: Single text or list of texts.
            normalize: Normalize embeddings.
            batch_size: Batch size.

        Returns:
            Numpy array of embeddings.
        """
        if isinstance(texts, str):
            texts = [texts]

        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embeddings = await self._async_call_ollama_embed(batch)
            all_embeddings.extend(embeddings)

        result = np.array(all_embeddings, dtype=np.float32)

        if normalize:
            norms = np.linalg.norm(result, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            result = result / norms

        return result

    def encode_query(self, query: str) -> np.ndarray:
        """Encode a query for retrieval.

        Args:
            query: Query text.

        Returns:
            Query embedding.
        """
        return self.encode(query)[0]

    def encode_documents(
        self,
        documents: list[str],
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> np.ndarray:
        """Encode documents for indexing.

        Args:
            documents: List of document texts.
            batch_size: Batch size.
            show_progress: Show progress (unused, kept for compatibility).

        Returns:
            Document embeddings.
        """
        return self.encode(
            documents,
            batch_size=batch_size,
        )

    def similarity(
        self,
        query_embedding: np.ndarray,
        document_embeddings: np.ndarray,
    ) -> np.ndarray:
        """Compute cosine similarity between query and documents.

        Args:
            query_embedding: Single query embedding.
            document_embeddings: Array of document embeddings.

        Returns:
            Similarity scores.
        """
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        if document_embeddings.ndim == 1:
            document_embeddings = document_embeddings.reshape(1, -1)

        similarities = np.dot(document_embeddings, query_embedding.T).flatten()
        return similarities

    def get_model_info(self) -> dict:
        """Get information about the loaded model.

        Returns:
            Model information dictionary.
        """
        return {
            "model_name": self.model_name,
            "ollama_base_url": self.ollama_base_url,
            "dimension": self.dimension,
        }

    def health_check(self) -> bool:
        """Check if embedding service is working.

        Returns:
            True if working.
        """
        try:
            test_embedding = self.encode("Kiểm tra embedding tiếng Việt")
            return len(test_embedding) > 0 and test_embedding.shape[-1] > 0
        except Exception as e:
            logger.error(f"Embedding health check failed: {e}")
            return False


# Global instance
_embedding_instance: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get global embedding service instance.

    Returns:
        EmbeddingService instance.
    """
    global _embedding_instance
    if _embedding_instance is None:
        _embedding_instance = EmbeddingService()
    return _embedding_instance
