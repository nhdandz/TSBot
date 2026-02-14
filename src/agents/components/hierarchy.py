"""Legal hierarchy navigation, smart selection, merging, and context building.

Uses in-memory chunk_map from vector_store for parent/child/sibling navigation.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from src.core.config import settings
from src.core.embeddings import get_embedding_service

logger = logging.getLogger(__name__)


# --- Legal Structure Formatting ---

def format_legal_path(metadata: Dict) -> str:
    """Format legal hierarchy path from metadata.

    Args:
        metadata: Chunk metadata dict.

    Returns:
        Formatted string like "Chuong X: Title".
    """
    parts = []

    chapter = metadata.get("chapter") or metadata.get("chapter_number")
    if chapter:
        title = metadata.get("chapter_title", "")
        parts.append(f"Chuong {chapter}" + (f": {title}" if title else ""))

    section = metadata.get("section") or metadata.get("section_number")
    if section:
        title = metadata.get("section_title", "")
        parts.append(f"Muc {section}" + (f": {title}" if title else ""))

    article = metadata.get("article") or metadata.get("article_number")
    if article:
        title = metadata.get("article_title", "")
        parts.append(f"Dieu {article}" + (f": {title}" if title else ""))

    clause = metadata.get("clause") or metadata.get("clause_number")
    if clause:
        parts.append(f"Khoan {clause}")

    point = metadata.get("point") or metadata.get("point_number")
    if point:
        parts.append(f"Diem {point}")

    return " > ".join(parts) if parts else ""


def build_legal_hierarchy_path(chunk: Dict) -> str:
    """Build full legal hierarchy path for a chunk.

    Args:
        chunk: Chunk dictionary.

    Returns:
        Path string like "Chuong VI > Muc 2 > Dieu 48 > Khoan 4".
    """
    metadata = chunk.get("metadata", {})
    return format_legal_path(metadata)


def _get_section_type(chunk: Dict) -> str:
    """Determine section type of a chunk.

    Args:
        chunk: Chunk dictionary.

    Returns:
        Section type string: chuong, muc, dieu, khoan, diem, or unknown.
    """
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


# --- Graph Navigation ---

def _get_chunk_map() -> Dict:
    """Get chunk_map from vector_store."""
    from src.agents.components.vector_store import get_store
    return get_store()["chunk_map"]


def find_parent_chunks(chunk: Dict, max_levels: int = 2) -> List[Dict]:
    """Find parent chunks up to max_levels.

    Args:
        chunk: Current chunk.
        max_levels: Maximum levels to traverse up.

    Returns:
        List of parent chunks (closest first).
    """
    chunk_map = _get_chunk_map()
    parents = []
    current = chunk

    for _ in range(max_levels):
        parent_id = current.get("metadata", {}).get("parent_id")
        if not parent_id or parent_id not in chunk_map:
            break
        parent = chunk_map[parent_id]
        parents.append(parent)
        current = parent

    return parents


def find_sibling_chunks(chunk: Dict, max_siblings: int = 2) -> List[Dict]:
    """Find sibling chunks (same parent).

    Args:
        chunk: Current chunk.
        max_siblings: Maximum siblings to return.

    Returns:
        List of sibling chunks.
    """
    chunk_map = _get_chunk_map()
    metadata = chunk.get("metadata", {})
    parent_id = metadata.get("parent_id")
    chunk_id = chunk.get("id") or metadata.get("chunk_id")

    if not parent_id or parent_id not in chunk_map:
        return []

    parent = chunk_map[parent_id]
    children_ids = parent.get("children_ids", [])

    siblings = []
    for cid in children_ids:
        if cid != chunk_id and cid in chunk_map:
            siblings.append(chunk_map[cid])
            if len(siblings) >= max_siblings:
                break

    return siblings


def find_children_chunks(chunk: Dict) -> List[Dict]:
    """Find all direct children of a chunk.

    Args:
        chunk: Current chunk.

    Returns:
        List of child chunks.
    """
    chunk_map = _get_chunk_map()
    children_ids = chunk.get("children_ids", [])
    return [chunk_map[cid] for cid in children_ids if cid in chunk_map]


# --- Smart Selection ---

def score_descendant_relevance(
    descendant: Dict,
    query: str,
    query_embedding: np.ndarray,
) -> float:
    """Score a descendant's relevance to the query.

    70% semantic similarity + 30% keyword overlap.

    Args:
        descendant: Descendant chunk.
        query: Original query.
        query_embedding: Query embedding vector.

    Returns:
        Relevance score between 0 and 1.
    """
    embedding_service = get_embedding_service()
    content = descendant.get("content", "")

    # Semantic score
    desc_embedding = embedding_service.encode_query(content)
    if query_embedding.ndim == 1:
        semantic_score = float(np.dot(query_embedding, desc_embedding))
    else:
        semantic_score = float(np.dot(query_embedding.flatten(), desc_embedding.flatten()))
    semantic_score = max(0.0, min(1.0, semantic_score))

    # Keyword score
    query_tokens = set(query.lower().split())
    content_tokens = set(content.lower().split())
    if query_tokens:
        overlap = len(query_tokens & content_tokens)
        keyword_score = overlap / len(query_tokens)
    else:
        keyword_score = 0.0

    return 0.7 * semantic_score + 0.3 * keyword_score


def find_smart_descendants(
    chunk: Dict,
    query: str,
    query_embedding: np.ndarray,
    max_descendants: int = None,
    min_score: float = None,
) -> List[Dict]:
    """Find relevant descendants using scoring.

    Args:
        chunk: Root chunk.
        query: Search query.
        query_embedding: Query embedding.
        max_descendants: Max descendants to return.
        min_score: Minimum relevance score.

    Returns:
        List of relevant descendant chunks with scores.
    """
    max_descendants = max_descendants or settings.max_smart_descendants
    min_score = min_score or settings.min_descendant_score

    chunk_map = _get_chunk_map()
    descendants = []

    # BFS to collect all descendants
    queue = list(chunk.get("children_ids", []))
    visited = set()

    while queue:
        child_id = queue.pop(0)
        if child_id in visited or child_id not in chunk_map:
            continue
        visited.add(child_id)

        child = chunk_map[child_id]
        descendants.append(child)

        # Add grandchildren
        queue.extend(child.get("children_ids", []))

    if not descendants:
        return []

    # Score and filter
    scored = []
    for desc in descendants:
        score = score_descendant_relevance(desc, query, query_embedding)
        if score >= min_score:
            desc["_relevance_score"] = score
            scored.append(desc)

    # Sort by score descending
    scored.sort(key=lambda x: x.get("_relevance_score", 0), reverse=True)
    return scored[:max_descendants]


def find_smart_siblings(
    chunk: Dict,
    query: str,
    query_embedding: np.ndarray,
    max_siblings: int = None,
    min_score: float = None,
) -> List[Dict]:
    """Find relevant sibling chunks using scoring.

    Args:
        chunk: Current chunk.
        query: Search query.
        query_embedding: Query embedding.
        max_siblings: Max siblings to return.
        min_score: Minimum relevance score.

    Returns:
        List of relevant sibling chunks with scores.
    """
    max_siblings = max_siblings or settings.max_smart_siblings
    min_score = min_score or settings.min_sibling_score

    siblings = find_sibling_chunks(chunk, max_siblings=10)

    if not siblings:
        return []

    scored = []
    for sib in siblings:
        score = score_descendant_relevance(sib, query, query_embedding)
        if score >= min_score:
            sib["_relevance_score"] = score
            scored.append(sib)

    scored.sort(key=lambda x: x.get("_relevance_score", 0), reverse=True)
    return scored[:max_siblings]


# --- Sibling Enrichment ---

def enrich_with_all_siblings(
    chunks: List[Dict],
    query: str,
    query_embedding: np.ndarray,
) -> List[Dict]:
    """Enrich retrieved chunks with ALL siblings for mid-level sections.

    For dieu/muc level chunks, add all siblings to provide complete context.

    Args:
        chunks: Retrieved chunks.
        query: Search query.
        query_embedding: Query embedding.

    Returns:
        Enriched list of chunks.
    """
    enriched = list(chunks)
    seen_ids = set()
    for c in chunks:
        cid = c.get("id") or c.get("metadata", {}).get("chunk_id")
        if cid:
            seen_ids.add(cid)

    for chunk in chunks:
        section_type = _get_section_type(chunk)

        # Only enrich mid-level sections (dieu, muc)
        if section_type not in ("dieu", "muc"):
            continue

        siblings = find_smart_siblings(chunk, query, query_embedding, max_siblings=5, min_score=0.3)

        for sib in siblings:
            sib_id = sib.get("id") or sib.get("metadata", {}).get("chunk_id")
            if sib_id and sib_id not in seen_ids:
                seen_ids.add(sib_id)
                sib["_is_sibling_enrichment"] = True
                enriched.append(sib)

    if len(enriched) > len(chunks):
        logger.info(f"Sibling enrichment: {len(chunks)} -> {len(enriched)} chunks")

    return enriched


# --- Smart Merging ---

def check_hierarchy_overlap(chunk1: Dict, chunk2: Dict) -> bool:
    """Check if chunk1 is an ancestor of chunk2 or vice versa.

    Args:
        chunk1: First chunk.
        chunk2: Second chunk.

    Returns:
        True if one is an ancestor of the other.
    """
    chunk_map = _get_chunk_map()

    # Check if chunk1 is ancestor of chunk2
    def is_ancestor(ancestor: Dict, descendant: Dict, max_depth: int = 5) -> bool:
        ancestor_id = ancestor.get("id") or ancestor.get("metadata", {}).get("chunk_id")
        current = descendant
        for _ in range(max_depth):
            parent_id = current.get("metadata", {}).get("parent_id")
            if not parent_id:
                return False
            if parent_id == ancestor_id:
                return True
            if parent_id not in chunk_map:
                return False
            current = chunk_map[parent_id]
        return False

    return is_ancestor(chunk1, chunk2) or is_ancestor(chunk2, chunk1)


def merge_chunks_smart(
    chunks: List[Dict],
    query: str,
    query_embedding: np.ndarray,
    context_settings: Dict = None,
) -> List[Dict]:
    """Smart merge: remove hierarchy overlaps and select best chunks.

    Args:
        chunks: Candidate chunks after reranking.
        query: Search query.
        query_embedding: Query embedding.
        context_settings: Adaptive context settings for current intent.

    Returns:
        Merged list of non-overlapping chunks.
    """
    if not chunks:
        return []

    max_chunks = (context_settings or {}).get("chunks", settings.max_chunks_multi)

    if len(chunks) <= 1:
        return chunks[:max_chunks]

    # Remove hierarchy overlaps: keep the more specific (deeper) chunk
    merged = [chunks[0]]

    for chunk in chunks[1:]:
        is_overlapping = False
        for existing in merged:
            if check_hierarchy_overlap(chunk, existing):
                is_overlapping = True
                # Keep the more specific one (deeper in hierarchy)
                chunk_depth = _get_depth(chunk)
                existing_depth = _get_depth(existing)
                if chunk_depth > existing_depth:
                    merged.remove(existing)
                    merged.append(chunk)
                break

        if not is_overlapping:
            merged.append(chunk)

        if len(merged) >= max_chunks:
            break

    return merged[:max_chunks]


def _get_depth(chunk: Dict) -> int:
    """Get hierarchy depth of a chunk (deeper = more specific)."""
    section_type = _get_section_type(chunk)
    depth_map = {"chuong": 1, "muc": 2, "dieu": 3, "khoan": 4, "diem": 5, "unknown": 0}
    return depth_map.get(section_type, 0)


# --- Context Building ---

def build_enriched_context(
    chunk: Dict,
    query: str,
    query_embedding: np.ndarray,
    context_settings: Dict = None,
) -> str:
    """Build enriched context for a single chunk with hierarchy.

    Includes: parent context + main content + descendants + siblings.

    Args:
        chunk: Main chunk.
        query: Search query.
        query_embedding: Query embedding.
        context_settings: Adaptive settings.

    Returns:
        Enriched context string.
    """
    cs = context_settings or settings.context_settings.get("general", {})
    parts = []

    # Legal path
    legal_path = build_legal_hierarchy_path(chunk)
    if legal_path:
        parts.append(f"[{legal_path}]")

    # Parent context
    if cs.get("include_parents", True):
        parents = find_parent_chunks(chunk, max_levels=2)
        for parent in reversed(parents):
            parent_content = parent.get("content", "")
            if parent_content:
                parent_path = build_legal_hierarchy_path(parent)
                prefix = f"[{parent_path}] " if parent_path else ""
                parts.append(f"Ngữ cảnh cấp trên: {prefix}{parent_content[:settings.parent_context_length]}")

    # Main content
    content = chunk.get("content", "")
    parts.append(f"Nội dung chính:\n{content}")

    # Smart descendants
    max_desc = cs.get("max_descendants", settings.max_smart_descendants)
    if max_desc > 0:
        descendants = find_smart_descendants(chunk, query, query_embedding, max_descendants=max_desc)
        if descendants:
            desc_parts = []
            for desc in descendants:
                desc_path = build_legal_hierarchy_path(desc)
                desc_content = desc.get("content", "")
                prefix = f"[{desc_path}] " if desc_path else ""
                desc_parts.append(f"  - {prefix}{desc_content}")
            parts.append("Các mục con liên quan:\n" + "\n".join(desc_parts))

    # Smart siblings
    max_sib = cs.get("max_siblings", settings.max_smart_siblings)
    if max_sib > 0:
        siblings = find_smart_siblings(chunk, query, query_embedding, max_siblings=max_sib)
        if siblings:
            sib_parts = []
            for sib in siblings:
                sib_path = build_legal_hierarchy_path(sib)
                sib_content = sib.get("content", "")
                prefix = f"[{sib_path}] " if sib_path else ""
                sib_parts.append(f"  - {prefix}{sib_content}")
            parts.append("Các mục cùng cấp:\n" + "\n".join(sib_parts))

    return "\n\n".join(parts)


def build_multi_chunk_context(
    chunks: List[Dict],
    query: str,
    query_embedding: np.ndarray,
    context_settings: Dict = None,
) -> str:
    """Build context from multiple chunks with enrichment.

    Args:
        chunks: List of merged/selected chunks.
        query: Search query.
        query_embedding: Query embedding.
        context_settings: Adaptive settings.

    Returns:
        Combined context string.
    """
    if not chunks:
        return ""

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        enriched = build_enriched_context(chunk, query, query_embedding, context_settings)
        context_parts.append(f"=== Nguồn {i} ===\n{enriched}")

    return "\n\n".join(context_parts)
