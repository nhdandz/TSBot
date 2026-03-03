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
        r"^(?:MỤC|Mục)\s+([IVXLCDM]+|\d+)[.:\s]*(.*)$",
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

    def _preprocess_legal_text(self, text: str) -> str:
        """Normalize whitespace và đảm bảo newline trước các điểm chữ (a) b) c)...).

        Chỉ xử lý letter-points. KHÔNG thêm newline trước số (1. 2. 3.) vì
        _chunk_article() dùng regex split trực tiếp, không cần newline delimiter.
        Tránh vô tình chèn newline vào "Điều 15.", "Khoản 3.", v.v.

        Args:
            text: Raw legal text.

        Returns:
            Preprocessed text với proper line breaks trước letter-points.
        """
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'([a-zđ]\)\s)', r'\n\1', text)
        return text.strip()

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
        # NOTE: _preprocess_legal_text() is applied per-article inside _chunk_article()
        # to avoid breaking article-level patterns (e.g. "Điều 15." → "Điều \n15.")
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
                # insert(index, object) - index first, then object
                articles.insert(0, (preamble, "0", "Phần mở đầu", 0))
        elif text.strip():
            # No articles found, treat entire text as one unit
            articles.append((text, "0", "", 0))

        return articles

    def _split_clause_by_points(self, clause_text: str) -> list[str]:
        """Split a clause text by letter-points (a) b) c)...) if it's too large.

        Args:
            clause_text: Text of a single clause.

        Returns:
            List of point-level segments. Returns [clause_text] if no points found
            or if all points fit within chunk_size.
        """
        point_pattern = re.compile(r"(?=^[a-zđ]\)\s)", re.MULTILINE)
        splits = point_pattern.split(clause_text)
        # Only use point-level splits when the clause is genuinely too large
        if len(splits) <= 1 or all(len(s) <= self.chunk_size for s in splits):
            return splits if len(splits) > 1 else [clause_text]
        return splits

    def _chunk_article(
        self,
        article_text: str,
        hierarchy: dict,
        doc_metadata: dict,
        base_pos: int,
    ) -> list[DocumentChunk]:
        """Chunk a single article that's too long.

        Splitting hierarchy:
        1. Preprocess article text (normalize whitespace, ensure newlines before khoản/điểm)
        2. Split by numeric clauses (Khoản: 1. 2. 3.)
        3. If a clause is too large → split by letter points (a) b) c)...)
           Each letter-point becomes its own chunk to avoid mixing conflicting rules.
        4. If a point is still too large → split at sentence boundary (. or ;)

        Args:
            article_text: Article content.
            hierarchy: Current document hierarchy.
            doc_metadata: Base metadata.
            base_pos: Starting position in original document.

        Returns:
            List of chunks.
        """
        chunks = []

        # Apply preprocess here (not at document level) to avoid breaking
        # article-level patterns like "Điều 15."
        article_text = self._preprocess_legal_text(article_text)

        # Level 1: split by numeric clauses (khoản)
        clause_pattern = re.compile(r"(?=^\d+\.\s)", re.MULTILINE)
        clause_splits = clause_pattern.split(article_text)

        current_chunk = ""
        current_clause = None
        chunk_start = base_pos

        def _flush_chunk(content: str):
            """Save accumulated content as a chunk."""
            if not content.strip():
                return
            meta = {
                **doc_metadata,
                **{k: v for k, v in hierarchy.items() if v is not None},
            }
            if current_clause:
                meta["clause"] = current_clause
            chunks.append(DocumentChunk(
                content=content.strip(),
                metadata=meta,
                start_pos=chunk_start,
                end_pos=chunk_start + len(content),
            ))

        for split in clause_splits:
            if not split.strip():
                continue

            # Extract clause number if present
            clause_match = self.CLAUSE_PATTERN.match(split)
            if clause_match:
                current_clause = clause_match.group(1)

            # Level 2: if clause is too large, split by letter-points
            if len(split) > self.chunk_size:
                point_splits = self._split_clause_by_points(split)

                if len(point_splits) > 1:
                    # Each letter-point becomes its own chunk (semantic unit)
                    # First: flush any accumulated content before these points
                    if current_chunk.strip():
                        _flush_chunk(current_chunk)
                        current_chunk = ""

                    for point_text in point_splits:
                        if not point_text.strip():
                            continue
                        # Level 3: if a point is still too large, sentence-boundary split
                        if len(point_text) > self.chunk_size:
                            remaining = point_text
                            while remaining:
                                break_point = self.chunk_size
                                for sep in [".\n", ";\n", ".", ";"]:
                                    pos = remaining.rfind(sep, 0, self.chunk_size)
                                    if pos > self.chunk_size // 2:
                                        break_point = pos + len(sep)
                                        break
                                _flush_chunk(remaining[:break_point])
                                remaining = remaining[break_point:]
                        else:
                            _flush_chunk(point_text)
                    continue

            # Normal accumulation for small clauses
            if len(current_chunk) + len(split) > self.chunk_size and current_chunk:
                _flush_chunk(current_chunk)
                overlap_text = current_chunk[-self.chunk_overlap:] if self.chunk_overlap else ""
                current_chunk = overlap_text + split
            else:
                current_chunk += split

        # Don't forget the last chunk
        if current_chunk.strip():
            _flush_chunk(current_chunk)

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
