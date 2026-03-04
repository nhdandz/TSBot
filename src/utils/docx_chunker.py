"""Paragraph-level chunker for Vietnamese legal .docx documents.

Reads each Word paragraph individually (không flatten sang string trước),
đảm bảo mỗi điểm a)/b)/c)/d) là một chunk riêng biệt, tránh trộn
các quy định xung đột vào cùng chunk.

Output format tương thích với vector_store.py, hierarchy.py, và reranker.py.
"""

import hashlib
import json
import logging
import re
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Thứ tự phân cấp (số nhỏ = cấp cao hơn)
HIERARCHY_LEVELS: Dict[str, int] = {
    'root':      0,
    'chuong':    1,
    'muc':       2,
    'dieu':      3,
    'khoan':     4,
    'item_abc':  5,
    'item_dash': 6,
    'item_plus': 7,
}

# Regex patterns phát hiện loại section
_SECTION_PATTERNS = [
    ('chuong',    r'^(?:CHƯƠNG|Chương)\s+([IVXLCDMivxlcdm]+)\.\s*(.*)$'),
    ('muc',       r'^(?:MỤC|Mục)\s+(\d+)\.\s*(.*)$'),
    ('dieu',      r'^(?:ĐIỀU|Điều)\s+(\d+)\.\s*(.*)$'),
    ('khoan',     r'^(\d+)\.\s+(.+)$'),
    ('item_abc',  r'^([a-zđ])\)\s*(.*)$'),
    ('item_dash', r'^[-–]\s+(.+)$'),
    ('item_plus', r'^\+\s+(.+)$'),
]


class DocxChunker:
    """Paragraph-level parser cho văn bản pháp lý .docx tiếng Việt.

    So với LegalDocumentChunker (regex-split trên raw text), cách tiếp cận này:
    - Đọc từng paragraph của Word document (đã có cấu trúc sẵn)
    - Mỗi điểm a)/b)/c)/d) tự nhiên là 1 paragraph → 1 chunk riêng
    - Không bao giờ ghép b) (quy định chung) và d) (ngoại lệ khu vực 1) vào cùng chunk

    Output: list[dict] với format tương thích vector_store.py:
        {
            "id": "abc123",
            "content": "b) Đối với các trường...",
            "metadata": {
                "chunk_id": "abc123",
                "section_type": "item_abc",
                "section_code": "III.2.15.2.b",
                "article": "15", "article_title": "Tiêu chuẩn tuyển sinh",
                "clause": "2", "point": "b",
                "chapter": "III", "chapter_title": "...",
                "parent_id": "...",
                "children_ids": [...],
                "sibling_ids": [...],
                ...
            }
        }
    """

    def __init__(self):
        self.chunks: List[Dict] = []
        # Stack: list of (section_type, section_number, chunk_id, section_title)
        self._stack: List[Tuple[str, str, str, str]] = []
        self._found_first_chapter = False
        self._global_context: List[str] = []
        self._position: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse_docx(
        self,
        docx_path: str,
        doc_metadata: Optional[Dict] = None,
    ) -> List[Dict]:
        """Parse .docx file thành chunks ở paragraph level.

        Args:
            docx_path: Đường dẫn tới file .docx.
            doc_metadata: Metadata bổ sung (source, document_type...).

        Returns:
            List chunk dicts tương thích vector_store.py.
        """
        try:
            from docx import Document
        except ImportError:
            raise ImportError("python-docx chưa được cài. Chạy: pip install python-docx")

        if doc_metadata is None:
            doc_metadata = {}
        doc_metadata.setdefault("source", Path(docx_path).name)

        doc = Document(docx_path)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        logger.info(f"[DocxChunker] {doc_metadata['source']}: {len(paragraphs)} paragraphs")

        # Root node — phần trước Chương I (điều khoản chung, tiêu đề...)
        root_id = self._make_id("root", "ROOT", -1)
        self._stack.append(("root", "ROOT", root_id, "Phần mở đầu"))

        current_section: Optional[Dict] = None
        current_content: List[str] = []

        def flush():
            if current_section and current_content:
                text = "\n".join(current_content)
                chunk = self._create_chunk(current_section, text, doc_metadata)
                self.chunks.append(chunk)

        for para in paragraphs:
            section_info = self._detect_section(para)

            if section_info:
                flush()

                # Khi gặp Chương I → đóng băng global context thành root chunk
                if (
                    section_info["type"] == "chuong"
                    and section_info["number"].upper() in ("I", "1")
                    and not self._found_first_chapter
                ):
                    self._found_first_chapter = True
                    if self._global_context:
                        root_chunk = self._make_root_chunk(
                            root_id, self._global_context, doc_metadata
                        )
                        self.chunks.insert(0, root_chunk)

                current_section = section_info
                current_content = [para]
            else:
                current_content.append(para)
                if not self._found_first_chapter:
                    self._global_context.append(para)

        flush()

        # Sau khi parse xong → build parent/children/sibling relationships
        self._build_relationships()

        logger.info(f"[DocxChunker] Done: {len(self.chunks)} chunks")
        return self.chunks

    def save_chunks_json(self, output_path: str):
        """Lưu chunks ra JSON file tương thích với vector_store.load_from_json().

        Args:
            output_path: Đường dẫn output (e.g. output_admission/chunks.json).
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        logger.info(f"[DocxChunker] Saved {len(self.chunks)} chunks → {output_path}")

    def print_summary(self):
        """In thống kê chunks theo section type."""
        counts: Dict[str, int] = defaultdict(int)
        for c in self.chunks:
            counts[c["metadata"]["section_type"]] += 1
        print(f"\n[DocxChunker] Tổng: {len(self.chunks)} chunks")
        for stype in sorted(counts):
            print(f"  {stype:12s}: {counts[stype]}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_id(section_type: str, content: str, position: int) -> str:
        raw = f"{section_type}_{content[:50]}_{position}"
        return str(uuid.UUID(hashlib.md5(raw.encode("utf-8")).hexdigest()))

    def _detect_section(self, text: str) -> Optional[Dict]:
        """Phát hiện loại section từ text của một paragraph."""
        text = text.strip()
        for section_type, pattern in _SECTION_PATTERNS:
            m = re.match(pattern, text, re.IGNORECASE)
            if not m:
                continue

            if section_type in ("item_dash", "item_plus"):
                return {
                    "type": section_type,
                    "number": text[0],
                    "title": m.group(1).strip(),
                    "full_text": text,
                }

            number = m.group(1)
            if section_type == "item_abc":
                number = number.lower()

            title = m.group(2).strip() if m.lastindex and m.lastindex >= 2 else ""
            return {
                "type": section_type,
                "number": number,
                "title": title,
                "full_text": text,
            }

        return None

    def _update_stack(self, section_type: str, number: str, chunk_id: str, title: str):
        """Cập nhật hierarchy stack khi gặp section mới.

        Pop tất cả phần tử có level >= current_level (cùng cấp hoặc sâu hơn),
        giữ lại parent có level < current_level.
        """
        current_level = HIERARCHY_LEVELS[section_type]
        while self._stack:
            top_type, _, _, _ = self._stack[-1]
            if HIERARCHY_LEVELS[top_type] < current_level:
                break
            self._stack.pop()
        self._stack.append((section_type, number, chunk_id, title))

    def _get_parent_id(self) -> Optional[str]:
        """Lấy chunk_id của parent (phần tử áp chót trong stack)."""
        if len(self._stack) >= 2:
            return self._stack[-2][2]
        return None

    def _build_section_code(self) -> str:
        """Xây dựng mã phân cấp ví dụ 'III.2.15.2.b'."""
        return ".".join(
            num for stype, num, _, _ in self._stack
            if stype != "root"
        )

    def _build_title_path(self) -> List[str]:
        """Xây dựng đường dẫn tiêu đề từ root đến current."""
        return [
            title or num
            for stype, num, _, title in self._stack
            if stype != "root"
        ]

    def _extract_hierarchy_keys(self) -> Dict:
        """Trích xuất các key phân cấp tương thích với hierarchy.py."""
        meta: Dict = {}
        for stype, num, _, title in self._stack:
            if stype == "chuong":
                meta["chapter"] = num
                if title:
                    meta["chapter_title"] = title
            elif stype == "muc":
                meta["section"] = num
                if title:
                    meta["section_title"] = title
            elif stype == "dieu":
                meta["article"] = num
                if title:
                    meta["article_title"] = title
            elif stype == "khoan":
                meta["clause"] = num
            elif stype == "item_abc":
                meta["point"] = num
        return meta

    def _get_module(self) -> str:
        """Lấy Chương hiện tại làm module."""
        for stype, num, _, _ in self._stack:
            if stype == "chuong":
                return f"Chương {num}"
        return "Root"

    def _create_chunk(
        self,
        section_info: Dict,
        content: str,
        doc_metadata: Dict,
    ) -> Dict:
        """Tạo một chunk dict từ section_info và content."""
        stype = section_info["type"]
        snumber = section_info["number"]
        stitle = section_info.get("title", "")

        chunk_id = self._make_id(stype, content, self._position)
        self._position += 1

        # Cập nhật stack TRƯỚC để _get_parent_id() trả về đúng parent
        self._update_stack(stype, snumber, chunk_id, stitle)
        parent_id = self._get_parent_id()
        section_code = self._build_section_code()
        title_path = self._build_title_path()
        hier_keys = self._extract_hierarchy_keys()
        module = self._get_module()

        metadata = {
            **doc_metadata,
            # --- DocxChunker-specific ---
            "chunk_id": chunk_id,
            "section_type": stype,
            "section_code": section_code,
            "section_number": snumber,
            "section_title": stitle,
            "title_path": title_path,
            "module": module,
            "level": len(self._stack) - 1,
            "position": self._position - 1,
            "is_global_context": not self._found_first_chapter,
            # --- hierarchy.py-compatible ---
            "parent_id": parent_id,
            "children_ids": [],   # filled in _build_relationships()
            "sibling_ids": [],    # filled in _build_relationships()
            **hier_keys,          # chapter, article, clause, point, *_title
        }

        return {
            "id": chunk_id,
            "content": content,
            "metadata": metadata,
        }

    @staticmethod
    def _make_root_chunk(root_id: str, lines: List[str], doc_metadata: Dict) -> Dict:
        """Tạo chunk cho phần mở đầu (trước Chương I)."""
        content = "\n".join(lines)
        return {
            "id": root_id,
            "content": content,
            "metadata": {
                **doc_metadata,
                "chunk_id": root_id,
                "section_type": "root",
                "section_code": "ROOT",
                "section_number": "ROOT",
                "section_title": "Phần mở đầu và quy định chung",
                "title_path": ["Root"],
                "module": "Root",
                "level": 0,
                "position": 0,
                "is_global_context": True,
                "parent_id": None,
                "children_ids": [],
                "sibling_ids": [],
            },
        }

    def _build_relationships(self):
        """Build children_ids và sibling_ids sau khi parse xong toàn bộ."""
        parent_children: Dict[str, List[str]] = defaultdict(list)

        for chunk in self.chunks:
            pid = chunk["metadata"].get("parent_id")
            if pid:
                parent_children[pid].append(chunk["id"])

        for chunk in self.chunks:
            cid = chunk["id"]
            pid = chunk["metadata"].get("parent_id")

            chunk["metadata"]["children_ids"] = parent_children.get(cid, [])

            if pid:
                siblings = [x for x in parent_children.get(pid, []) if x != cid]
                chunk["metadata"]["sibling_ids"] = siblings
