"""Structure-aware chunking for Vietnamese legal documents."""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class DocumentChunk:
    """A chunk of text from a legal document."""

    content: str
    metadata: dict
    start_pos: int
    end_pos: int

    @property
    def char_count(self) -> int:
        return len(self.content)


class LegalDocumentChunker:
    """Chunker optimized for Vietnamese legal/regulatory documents.

    Recognizes structure like:
    - Chương (Chapter)
    - Điều (Article)
    - Khoản (Clause)
    - Điểm (Point)
    - Mục (Section)
    """

    # Patterns for document structure
    CHAPTER_PATTERN = re.compile(
        r"^(?:CHƯƠNG|Chương)\s+([IVXLCDM]+|\d+)[.:\s]*(.*)$",
        re.MULTILINE | re.IGNORECASE,
    )

    ARTICLE_PATTERN = re.compile(
        r"^(?:ĐIỀU|Điều)\s+(\d+)[.:\s]*(.*)$",
        re.MULTILINE | re.IGNORECASE,
    )

    CLAUSE_PATTERN = re.compile(
        r"^(\d+)[.]\s+(.+)$",
        re.MULTILINE,
    )

    POINT_PATTERN = re.compile(
        r"^([a-z])[)]\s+(.+)$",
        re.MULTILINE,
    )

    SECTION_PATTERN = re.compile(
        r"^(?:MỤC|Mục)\s+(\d+)[.:\s]*(.*)$",
        re.MULTILINE | re.IGNORECASE,
    )

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        respect_structure: bool = True,
        include_hierarchy: bool = True,
    ):
        """Initialize chunker.

        Args:
            chunk_size: Target chunk size in characters.
            chunk_overlap: Overlap between chunks.
            respect_structure: Try to keep structural units together.
            include_hierarchy: Include hierarchy info in metadata.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.respect_structure = respect_structure
        self.include_hierarchy = include_hierarchy

    def chunk_document(
        self,
        text: str,
        doc_metadata: Optional[dict] = None,
    ) -> list[DocumentChunk]:
        """Chunk a legal document.

        Args:
            text: Document text.
            doc_metadata: Additional metadata to include.

        Returns:
            List of document chunks.
        """
        if doc_metadata is None:
            doc_metadata = {}

        if self.respect_structure:
            return self._structure_aware_chunk(text, doc_metadata)
        else:
            return self._simple_chunk(text, doc_metadata)

    def _structure_aware_chunk(
        self,
        text: str,
        doc_metadata: dict,
    ) -> list[DocumentChunk]:
        """Chunk while respecting document structure.

        Args:
            text: Document text.
            doc_metadata: Base metadata.

        Returns:
            List of chunks.
        """
        chunks = []
        current_hierarchy = {
            "chapter": None,
            "chapter_title": None,
            "section": None,
            "section_title": None,
            "article": None,
            "article_title": None,
        }

        # Split by articles first (main structural unit)
        article_splits = self._split_by_articles(text)

        for article_text, article_num, article_title, start_pos in article_splits:
            # Update hierarchy
            current_hierarchy["article"] = article_num
            current_hierarchy["article_title"] = article_title

            # Find chapter/section context from preceding text
            chapter_match = None
            section_match = None

            # Look backwards in original text for chapter
            preceding = text[:start_pos]
            chapter_matches = list(self.CHAPTER_PATTERN.finditer(preceding))
            if chapter_matches:
                last_chapter = chapter_matches[-1]
                current_hierarchy["chapter"] = last_chapter.group(1)
                current_hierarchy["chapter_title"] = last_chapter.group(2).strip()

            section_matches = list(self.SECTION_PATTERN.finditer(preceding))
            if section_matches:
                last_section = section_matches[-1]
                current_hierarchy["section"] = last_section.group(1)
                current_hierarchy["section_title"] = last_section.group(2).strip()

            # Chunk article content
            if len(article_text) <= self.chunk_size:
                # Article fits in one chunk
                metadata = {
                    **doc_metadata,
                    **{k: v for k, v in current_hierarchy.items() if v is not None},
                }
                chunks.append(
                    DocumentChunk(
                        content=article_text.strip(),
                        metadata=metadata,
                        start_pos=start_pos,
                        end_pos=start_pos + len(article_text),
                    )
                )
            else:
                # Split article into smaller chunks
                article_chunks = self._chunk_article(
                    article_text, current_hierarchy, doc_metadata, start_pos
                )
                chunks.extend(article_chunks)

        return chunks

    def _split_by_articles(
        self, text: str
    ) -> list[tuple[str, str, str, int]]:
        """Split document by articles.

        Returns:
            List of (article_text, article_number, article_title, start_position).
        """
        articles = []
        matches = list(self.ARTICLE_PATTERN.finditer(text))

        for i, match in enumerate(matches):
            start_pos = match.start()
            article_num = match.group(1)
            article_title = match.group(2).strip()

            # Determine end position
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(text)

            article_text = text[start_pos:end_pos]
            articles.append((article_text, article_num, article_title, start_pos))

        # Handle text before first article
        if matches:
            preamble = text[: matches[0].start()].strip()
            if preamble and len(preamble) > 50:  # Meaningful preamble
                articles.insert(
                    (preamble, "0", "Phần mở đầu", 0), 0  # type: ignore
                )
        elif text.strip():
            # No articles found, treat entire text as one unit
            articles.append((text, "0", "", 0))

        return articles

    def _chunk_article(
        self,
        article_text: str,
        hierarchy: dict,
        doc_metadata: dict,
        base_pos: int,
    ) -> list[DocumentChunk]:
        """Chunk a single article that's too long.

        Args:
            article_text: Article content.
            hierarchy: Current document hierarchy.
            doc_metadata: Base metadata.
            base_pos: Starting position in original document.

        Returns:
            List of chunks.
        """
        chunks = []

        # Try to split by clauses (khoản)
        clause_pattern = re.compile(r"(?=^\d+\.\s)", re.MULTILINE)
        clause_splits = clause_pattern.split(article_text)

        current_chunk = ""
        current_clause = None
        chunk_start = base_pos

        for split in clause_splits:
            if not split.strip():
                continue

            # Extract clause number if present
            clause_match = self.CLAUSE_PATTERN.match(split)
            if clause_match:
                current_clause = clause_match.group(1)

            # Check if adding this would exceed chunk size
            if len(current_chunk) + len(split) > self.chunk_size and current_chunk:
                # Save current chunk
                metadata = {
                    **doc_metadata,
                    **{k: v for k, v in hierarchy.items() if v is not None},
                }
                if current_clause:
                    metadata["clause"] = current_clause

                chunks.append(
                    DocumentChunk(
                        content=current_chunk.strip(),
                        metadata=metadata,
                        start_pos=chunk_start,
                        end_pos=chunk_start + len(current_chunk),
                    )
                )

                # Start new chunk with overlap
                overlap_text = current_chunk[-self.chunk_overlap :] if self.chunk_overlap else ""
                current_chunk = overlap_text + split
                chunk_start = chunk_start + len(current_chunk) - len(overlap_text) - len(split)
            else:
                current_chunk += split

        # Don't forget the last chunk
        if current_chunk.strip():
            metadata = {
                **doc_metadata,
                **{k: v for k, v in hierarchy.items() if v is not None},
            }
            if current_clause:
                metadata["clause"] = current_clause

            chunks.append(
                DocumentChunk(
                    content=current_chunk.strip(),
                    metadata=metadata,
                    start_pos=chunk_start,
                    end_pos=chunk_start + len(current_chunk),
                )
            )

        return chunks

    def _simple_chunk(
        self,
        text: str,
        doc_metadata: dict,
    ) -> list[DocumentChunk]:
        """Simple character-based chunking with overlap.

        Args:
            text: Document text.
            doc_metadata: Base metadata.

        Returns:
            List of chunks.
        """
        chunks = []
        text = text.strip()

        start = 0
        while start < len(text):
            end = start + self.chunk_size

            # Try to find a good break point (end of sentence)
            if end < len(text):
                # Look for sentence endings
                break_chars = [".", "。", "\n\n", "\n"]
                best_break = end

                for char in break_chars:
                    pos = text.rfind(char, start, end)
                    if pos > start + self.chunk_size // 2:
                        best_break = pos + len(char)
                        break

                end = best_break

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    DocumentChunk(
                        content=chunk_text,
                        metadata={
                            **doc_metadata,
                            "chunk_index": len(chunks),
                        },
                        start_pos=start,
                        end_pos=end,
                    )
                )

            # Move to next chunk with overlap
            start = end - self.chunk_overlap if end < len(text) else end

        return chunks

    def get_hierarchy_path(self, chunk: DocumentChunk) -> str:
        """Get a readable hierarchy path for a chunk.

        Args:
            chunk: Document chunk.

        Returns:
            Hierarchy path string.
        """
        parts = []

        if chunk.metadata.get("chapter"):
            parts.append(f"Chương {chunk.metadata['chapter']}")
        if chunk.metadata.get("section"):
            parts.append(f"Mục {chunk.metadata['section']}")
        if chunk.metadata.get("article"):
            parts.append(f"Điều {chunk.metadata['article']}")
        if chunk.metadata.get("clause"):
            parts.append(f"Khoản {chunk.metadata['clause']}")

        return " > ".join(parts) if parts else "N/A"
