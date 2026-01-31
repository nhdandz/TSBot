"""Vietnamese embedding service for TSBot."""

import logging
from typing import Optional

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from src.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Embedding service optimized for Vietnamese text."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        fallback_model: Optional[str] = None,
        device: Optional[str] = None,
    ):
        """Initialize embedding service.

        Args:
            model_name: Primary embedding model name.
            fallback_model: Fallback model if primary fails.
            device: Device to use (cuda/cpu). Auto-detected if None.
        """
        self.model_name = model_name or settings.embedding_model
        self.fallback_model = fallback_model or settings.embedding_fallback_model

        # Auto-detect device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self._model: Optional[SentenceTransformer] = None
        self._dimension: Optional[int] = None

    @property
    def model(self) -> SentenceTransformer:
        """Get or load the embedding model."""
        if self._model is None:
            self._model = self._load_model()
        return self._model

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        if self._dimension is None:
            # Generate a test embedding to get dimension
            test_embedding = self.model.encode("test", convert_to_numpy=True)
            self._dimension = len(test_embedding)
        return self._dimension

    def _load_model(self) -> SentenceTransformer:
        """Load embedding model with fallback support.

        Returns:
            Loaded SentenceTransformer model.
        """
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            model = SentenceTransformer(
                self.model_name,
                device=self.device,
                trust_remote_code=True,
            )
            logger.info(f"Model loaded successfully on {self.device}")
            return model

        except Exception as e:
            logger.warning(f"Failed to load primary model: {e}")
            logger.info(f"Trying fallback model: {self.fallback_model}")

            try:
                # Try fallback model
                model = SentenceTransformer(
                    self.fallback_model,
                    device=self.device,
                )
                logger.info("Fallback model loaded successfully")
                return model

            except Exception as e2:
                logger.error(f"Failed to load fallback model: {e2}")
                raise RuntimeError(
                    f"Could not load any embedding model. "
                    f"Primary: {self.model_name}, Fallback: {self.fallback_model}"
                )

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
            show_progress: Show progress bar.

        Returns:
            Numpy array of embeddings.
        """
        if isinstance(texts, str):
            texts = [texts]

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=normalize,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )

        return embeddings

    async def aencode(
        self,
        texts: str | list[str],
        normalize: bool = True,
        batch_size: int = 32,
    ) -> np.ndarray:
        """Async encode texts to embeddings.

        Note: Uses sync encoding under the hood with thread pool.

        Args:
            texts: Single text or list of texts.
            normalize: Normalize embeddings.
            batch_size: Batch size.

        Returns:
            Numpy array of embeddings.
        """
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.encode(texts, normalize, batch_size),
        )

    def encode_query(self, query: str) -> np.ndarray:
        """Encode a query for retrieval.

        Some models use different prefixes for queries vs documents.

        Args:
            query: Query text.

        Returns:
            Query embedding.
        """
        # Check if model supports query prefix (like BGE models)
        if hasattr(self.model, "_first_module"):
            module = self.model._first_module()
            if hasattr(module, "tokenizer"):
                # BGE models use "query: " prefix
                if "bge" in self.model_name.lower():
                    query = f"query: {query}"

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
            show_progress: Show progress.

        Returns:
            Document embeddings.
        """
        return self.encode(
            documents,
            batch_size=batch_size,
            show_progress=show_progress,
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
        # Ensure 2D arrays
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        if document_embeddings.ndim == 1:
            document_embeddings = document_embeddings.reshape(1, -1)

        # Cosine similarity (embeddings are already normalized)
        similarities = np.dot(document_embeddings, query_embedding.T).flatten()
        return similarities

    def get_model_info(self) -> dict:
        """Get information about the loaded model.

        Returns:
            Model information dictionary.
        """
        return {
            "model_name": self.model_name,
            "device": self.device,
            "dimension": self.dimension,
            "max_seq_length": getattr(self.model, "max_seq_length", "unknown"),
        }

    def health_check(self) -> bool:
        """Check if embedding service is working.

        Returns:
            True if working.
        """
        try:
            test_embedding = self.encode("Kiểm tra embedding tiếng Việt")
            return len(test_embedding) > 0 and test_embedding.shape[-1] == self.dimension
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
