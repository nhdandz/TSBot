"""In-memory vector store with chunk_map for hierarchy navigation.

Complements Qdrant (dense search) with in-memory chunk_map for
parent/child/sibling navigation and BM25 sparse search.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from src.core.config import settings
from src.core.embeddings import get_embedding_service

logger = logging.getLogger(__name__)

# Global vector store state
_store: Dict[str, Any] = {
    "chunks": [],
    "embeddings": None,
    "chunk_map": {},
    "semantic_cache": [],
    "loaded": False,
}


def get_store() -> Dict[str, Any]:
    """Get the global vector store."""
    return _store


def clear_store():
    """Clear all data from the store."""
    _store["chunks"] = []
    _store["embeddings"] = None
    _store["chunk_map"] = {}
    _store["semantic_cache"] = []
    _store["loaded"] = False


def build_enriched_text_for_embedding(chunk: Dict) -> str:
    """Build enriched text for embedding with parent context and title path.

    Args:
        chunk: Chunk dictionary with metadata.

    Returns:
        Enriched text string for embedding.
    """
    metadata = chunk.get("metadata", {})
    content = chunk.get("content", "")
    parts = []

    # Title path (legal hierarchy)
    title_parts = []
    for level in ["chapter_title", "section_title", "article_title"]:
        title = metadata.get(level, "")
        if title:
            title_parts.append(title)
    if title_parts:
        parts.append(" > ".join(title_parts[-settings.title_path_levels:]))

    # Parent context
    parent_id = metadata.get("parent_id")
    if parent_id and parent_id in _store["chunk_map"]:
        parent = _store["chunk_map"][parent_id]
        parent_content = parent.get("content", "")
        if parent_content:
            parts.append(parent_content[:settings.parent_context_length])

    # Main content
    parts.append(content)

    return " | ".join(parts)


def _build_chunk_map(chunks: List[Dict]):
    """Build chunk_map for hierarchy navigation.

    Args:
        chunks: List of chunk dictionaries.
    """
    chunk_map = {}
    for chunk in chunks:
        chunk_id = chunk.get("id") or chunk.get("metadata", {}).get("chunk_id")
        if chunk_id:
            chunk_map[chunk_id] = chunk

    # Build parent-children relationships
    for chunk_id, chunk in chunk_map.items():
        metadata = chunk.get("metadata", {})
        parent_id = metadata.get("parent_id")
        if parent_id and parent_id in chunk_map:
            parent = chunk_map[parent_id]
            if "children_ids" not in parent:
                parent["children_ids"] = []
            if chunk_id not in parent["children_ids"]:
                parent["children_ids"].append(chunk_id)

    _store["chunk_map"] = chunk_map
    logger.info(f"Built chunk_map with {len(chunk_map)} entries")


def load_from_json(json_path: Optional[str] = None) -> Dict[str, Any]:
    """Load chunks from JSON file, build chunk_map, generate embeddings, upsert Qdrant.

    Args:
        json_path: Path to chunks JSON file.

    Returns:
        Stats dictionary.
    """
    path = Path(json_path or settings.chunks_json_path)
    if not path.exists():
        raise FileNotFoundError(f"Chunks file not found: {path}")

    logger.info(f"Loading chunks from {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Support both list format and dict with "chunks" key
    if isinstance(data, dict):
        chunks = data.get("chunks", [])
    else:
        chunks = data

    if not chunks:
        raise ValueError("No chunks found in JSON file")

    logger.info(f"Loaded {len(chunks)} chunks from JSON")

    # Store chunks
    _store["chunks"] = chunks

    # Build chunk_map
    _build_chunk_map(chunks)

    # Generate embeddings
    embedding_service = get_embedding_service()

    if settings.use_enriched_embeddings:
        texts = [build_enriched_text_for_embedding(c) for c in chunks]
        logger.info("Using enriched embeddings with parent context + title path")
    else:
        texts = [c.get("content", "") for c in chunks]

    logger.info(f"Generating embeddings for {len(texts)} chunks...")
    embeddings = embedding_service.encode_documents(texts, batch_size=32, show_progress=False)
    _store["embeddings"] = embeddings
    logger.info(f"Generated embeddings shape: {embeddings.shape}")

    # Upsert to Qdrant
    _upsert_to_qdrant(chunks, embeddings)

    _store["loaded"] = True

    return {
        "total_chunks": len(chunks),
        "chunk_map_size": len(_store["chunk_map"]),
        "embeddings_shape": list(embeddings.shape),
    }


def _upsert_to_qdrant(chunks: List[Dict], embeddings: np.ndarray):
    """Upsert chunks and embeddings to Qdrant.

    Args:
        chunks: List of chunk dictionaries.
        embeddings: Embedding matrix.
    """
    from src.database.qdrant import get_qdrant_db
    import asyncio

    qdrant = get_qdrant_db()

    vectors = []
    payloads = []
    ids = []

    for i, chunk in enumerate(chunks):
        chunk_id = chunk.get("id") or chunk.get("metadata", {}).get("chunk_id") or str(i)
        metadata = chunk.get("metadata", {})
        content = chunk.get("content", "")

        payload = {
            "content": content,
            "chunk_id": chunk_id,
            **metadata,
        }

        vectors.append(embeddings[i].tolist())
        payloads.append(payload)
        ids.append(str(chunk_id))

    # Run async upsert
    async def _do_upsert():
        await qdrant.create_collection(
            collection_name=settings.qdrant_legal_collection,
            vector_size=settings.embedding_dimension,
        )
        # Upsert in batches
        batch_size = 100
        for start in range(0, len(vectors), batch_size):
            end = min(start + batch_size, len(vectors))
            await qdrant.upsert_vectors(
                collection_name=settings.qdrant_legal_collection,
                vectors=vectors[start:end],
                payloads=payloads[start:end],
                ids=ids[start:end],
            )
            logger.info(f"Upserted batch {start}-{end} to Qdrant")

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_do_upsert())
            logger.info("Qdrant upsert scheduled (async)")
        else:
            loop.run_until_complete(_do_upsert())
    except RuntimeError:
        asyncio.run(_do_upsert())

    logger.info(f"Upserted {len(vectors)} vectors to Qdrant collection '{settings.qdrant_legal_collection}'")


async def async_load_from_json(json_path: Optional[str] = None) -> Dict[str, Any]:
    """Async version of load_from_json for use in async context (e.g., FastAPI startup).

    Args:
        json_path: Path to chunks JSON file.

    Returns:
        Stats dictionary.
    """
    path = Path(json_path or settings.chunks_json_path)
    if not path.exists():
        raise FileNotFoundError(f"Chunks file not found: {path}")

    logger.info(f"[async] Loading chunks from {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        chunks = data.get("chunks", [])
    else:
        chunks = data

    if not chunks:
        raise ValueError("No chunks found in JSON file")

    logger.info(f"Loaded {len(chunks)} chunks from JSON")
    _store["chunks"] = chunks
    _build_chunk_map(chunks)

    # Generate embeddings
    embedding_service = get_embedding_service()

    if settings.use_enriched_embeddings:
        texts = [build_enriched_text_for_embedding(c) for c in chunks]
    else:
        texts = [c.get("content", "") for c in chunks]

    logger.info(f"Generating embeddings for {len(texts)} chunks...")
    embeddings = embedding_service.encode_documents(texts, batch_size=32, show_progress=False)
    _store["embeddings"] = embeddings
    logger.info(f"Generated embeddings shape: {embeddings.shape}")

    # Upsert to Qdrant
    from src.database.qdrant import get_qdrant_db
    qdrant = get_qdrant_db()

    vectors = []
    payloads = []
    ids = []

    for i, chunk in enumerate(chunks):
        chunk_id = chunk.get("id") or chunk.get("metadata", {}).get("chunk_id") or str(i)
        metadata = chunk.get("metadata", {})
        content = chunk.get("content", "")

        payload = {"content": content, "chunk_id": chunk_id, **metadata}
        vectors.append(embeddings[i].tolist())
        payloads.append(payload)
        ids.append(str(chunk_id))

    await qdrant.create_collection(
        collection_name=settings.qdrant_legal_collection,
        vector_size=settings.embedding_dimension,
    )

    batch_size = 100
    for start in range(0, len(vectors), batch_size):
        end = min(start + batch_size, len(vectors))
        await qdrant.upsert_vectors(
            collection_name=settings.qdrant_legal_collection,
            vectors=vectors[start:end],
            payloads=payloads[start:end],
            ids=ids[start:end],
        )
        logger.info(f"Upserted batch {start}-{end} to Qdrant")

    _store["loaded"] = True

    return {
        "total_chunks": len(chunks),
        "chunk_map_size": len(_store["chunk_map"]),
        "embeddings_shape": list(embeddings.shape),
    }


async def auto_load_chunks():
    """Auto-load chunks on startup if JSON file exists."""
    path = Path(settings.chunks_json_path)
    if path.exists():
        try:
            stats = await async_load_from_json()
            logger.info(f"Auto-loaded chunks: {stats}")
        except Exception as e:
            logger.warning(f"Failed to auto-load chunks: {e}")
    else:
        logger.info(f"No chunks file found at {path}, skipping auto-load")
