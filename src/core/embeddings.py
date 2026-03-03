"""Embedding service dùng sentence-transformers chạy local trên GPU.

Model bge-m3 được load trực tiếp vào máy application (16GB GPU).
Không cần Ollama cho embeddings.
"""

import asyncio
import logging
from typing import Optional

import numpy as np

from src.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Embedding service dùng sentence-transformers với GPU acceleration."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
    ):
        """Khởi tạo embedding service.

        Args:
            model_name: HuggingFace model name (mặc định BAAI/bge-m3).
            device: "cuda", "cpu", hoặc "auto" (tự detect).
        """
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name or settings.embedding_model
        resolved_device = device or settings.embedding_device

        if resolved_device == "auto":
            import torch
            resolved_device = "cuda" if torch.cuda.is_available() else "cpu"

        self.device = resolved_device

        logger.info(f"Loading embedding model '{self.model_name}' on device '{self.device}'")
        self._model = SentenceTransformer(self.model_name, device=self.device)
        logger.info(f"Embedding model loaded. Dimension: {self._model.get_sentence_embedding_dimension()}")

    @property
    def dimension(self) -> int:
        """Dimension của embedding vectors."""
        return self._model.get_sentence_embedding_dimension()

    def encode(
        self,
        texts: str | list[str],
        normalize: bool = True,
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> np.ndarray:
        """Encode texts thành embedding vectors (synchronous).

        Args:
            texts: Single text hoặc list of texts.
            normalize: Normalize về unit length.
            batch_size: Batch size khi encode nhiều texts.
            show_progress: Hiện progress bar.

        Returns:
            numpy array shape (N, dimension) hoặc (dimension,) nếu single text.
        """
        single = isinstance(texts, str)
        if single:
            texts = [texts]

        embeddings = self._model.encode(
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
        """Async encode texts — chạy trong thread executor để không block event loop.

        Args:
            texts: Single text hoặc list of texts.
            normalize: Normalize về unit length.
            batch_size: Batch size.

        Returns:
            numpy array of embeddings.
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.encode(texts, normalize=normalize, batch_size=batch_size),
        )
        return result

    def encode_query(self, query: str) -> np.ndarray:
        """Encode single query string. Trả về 1D array (dimension,)."""
        result = self.encode(query)
        return result[0]

    def encode_documents(
        self,
        documents: list[str],
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> np.ndarray:
        """Encode nhiều documents. Trả về 2D array (N, dimension)."""
        return self.encode(documents, batch_size=batch_size, show_progress=show_progress)

    def similarity(
        self,
        query_embedding: np.ndarray,
        document_embeddings: np.ndarray,
    ) -> np.ndarray:
        """Tính cosine similarity giữa query và documents.

        Args:
            query_embedding: 1D hoặc 2D array.
            document_embeddings: 2D array (N, dimension).

        Returns:
            Similarity scores 1D array.
        """
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        if document_embeddings.ndim == 1:
            document_embeddings = document_embeddings.reshape(1, -1)

        return np.dot(document_embeddings, query_embedding.T).flatten()

    def get_model_info(self) -> dict:
        """Thông tin về model đang dùng."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "dimension": self.dimension,
        }

    def health_check(self) -> bool:
        """Kiểm tra embedding service hoạt động bình thường."""
        try:
            test = self.encode("Kiểm tra embedding tiếng Việt")
            return test.shape[-1] == self.dimension
        except Exception as e:
            logger.error(f"Embedding health check failed: {e}")
            return False


# Global instance — load model 1 lần duy nhất khi khởi động
_embedding_instance: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Lấy global embedding service instance."""
    global _embedding_instance
    if _embedding_instance is None:
        _embedding_instance = EmbeddingService()
    return _embedding_instance
