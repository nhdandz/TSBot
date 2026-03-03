"""Script to index legal documents into Qdrant vector database."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
from src.core.embeddings import get_embedding_service
from src.database.qdrant import get_qdrant_db
from src.utils.chunking import LegalDocumentChunker
from src.utils.docx_chunker import DocxChunker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_text_file(file_path: Path) -> str:
    """Read text from .txt and .pdf files."""
    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        return file_path.read_text(encoding="utf-8")

    elif suffix == ".pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(file_path)
            text = []
            for page in reader.pages:
                text.append(page.extract_text())
            return "\n".join(text)
        except ImportError:
            logger.warning("pypdf not installed, skipping .pdf files")
            return ""

    return ""


def chunks_from_docx(doc_path: Path, doc_metadata: dict) -> list[dict]:
    """Parse .docx với DocxChunker (paragraph-level, mỗi a)/b)/c) là chunk riêng).

    Args:
        doc_path: Đường dẫn file .docx.
        doc_metadata: Metadata bổ sung (source, file_path...).

    Returns:
        List chunk dicts: [{"id": ..., "content": ..., "metadata": {...}}, ...]
    """
    chunker = DocxChunker()
    chunks = chunker.parse_docx(str(doc_path), doc_metadata)

    # Lưu chunks.json để hierarchy.py và RAG agent có thể dùng offline
    chunks_json_path = Path(settings.chunks_json_path)
    chunks_json_path.parent.mkdir(parents=True, exist_ok=True)
    chunker.save_chunks_json(str(chunks_json_path))
    chunker.print_summary()

    return chunks


async def index_documents(
    documents_dir: Path,
    batch_size: int = 32,
    force_reindex: bool = False,
):
    """Index documents from directory into Qdrant.

    .docx  → DocxChunker (paragraph-level, hierarchy-aware)
    .txt / .pdf → LegalDocumentChunker (regex-split fallback)

    Args:
        documents_dir: Directory containing documents.
        batch_size: Batch size for embedding.
        force_reindex: Force re-indexing even if already exists.
    """
    logger.info(f"Indexing documents from: {documents_dir}")

    # Initialize services
    embedding_service = get_embedding_service()
    qdrant = get_qdrant_db()
    fallback_chunker = LegalDocumentChunker(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
        respect_structure=True,
    )

    # Create collection
    await qdrant.create_collection(
        collection_name=settings.qdrant_legal_collection,
        vector_size=embedding_service.dimension,
    )

    # Check if already indexed
    if not force_reindex:
        count = await qdrant.count_points(settings.qdrant_legal_collection)
        if count > 0:
            logger.info(f"Collection already has {count} documents. Use --force to reindex.")
            return

    # Find all documents
    supported_extensions = {".txt", ".docx", ".pdf"}
    document_files = [
        f for f in documents_dir.iterdir()
        if f.is_file() and f.suffix.lower() in supported_extensions
    ]

    if not document_files:
        logger.warning(f"No documents found in {documents_dir}")
        return

    logger.info(f"Found {len(document_files)} documents to index")

    # ----------------------------------------------------------------
    # Unified chunk list — mỗi phần tử là dict {"id", "content", "metadata"}
    # ----------------------------------------------------------------
    all_chunk_dicts: list[dict] = []
    all_embeddings: list[list[float]] = []

    for doc_path in document_files:
        logger.info(f"Processing: {doc_path.name}")

        doc_metadata = {
            "source": doc_path.name,
            "file_path": str(doc_path),
        }

        # --- .docx: dùng DocxChunker paragraph-level ---
        if doc_path.suffix.lower() == ".docx":
            try:
                chunk_dicts = chunks_from_docx(doc_path, doc_metadata)
                logger.info(f"  [DocxChunker] {len(chunk_dicts)} chunks")
            except Exception as e:
                logger.error(f"  DocxChunker failed: {e}. Falling back to text chunker.")
                chunk_dicts = []

            if not chunk_dicts:
                # Fallback: đọc text thô rồi dùng LegalDocumentChunker
                try:
                    from docx import Document as _Document
                    raw_text = "\n".join(p.text for p in _Document(doc_path).paragraphs)
                except ImportError:
                    raw_text = ""
                if raw_text.strip():
                    fallback_chunks = fallback_chunker.chunk_document(raw_text, doc_metadata)
                    chunk_dicts = [
                        {
                            "id": f"fallback_{doc_path.stem}_{i}",
                            "content": c.content,
                            "metadata": c.metadata,
                        }
                        for i, c in enumerate(fallback_chunks)
                    ]
                    logger.info(f"  [Fallback] {len(chunk_dicts)} chunks")

        # --- .txt / .pdf: dùng LegalDocumentChunker ---
        else:
            text = read_text_file(doc_path)
            if not text.strip():
                logger.warning(f"  Empty or unreadable: {doc_path.name}")
                continue
            legacy_chunks = fallback_chunker.chunk_document(text, doc_metadata)
            chunk_dicts = [
                {
                    "id": f"{doc_path.stem}_{i}",
                    "content": c.content,
                    "metadata": c.metadata,
                }
                for i, c in enumerate(legacy_chunks)
            ]
            logger.info(f"  [LegalDocumentChunker] {len(chunk_dicts)} chunks")

        # --- Embed theo batch ---
        texts = [cd["content"] for cd in chunk_dicts]
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_embeddings = embedding_service.encode_documents(batch_texts)
            for j, emb in enumerate(batch_embeddings):
                all_chunk_dicts.append(chunk_dicts[i + j])
                all_embeddings.append(emb.tolist())

    if not all_chunk_dicts:
        logger.warning("No chunks to index")
        return

    # ----------------------------------------------------------------
    # Upsert to Qdrant
    # Qdrant chỉ nhận integer hoặc UUID làm point ID.
    # DocxChunker tạo 16-char MD5 hex → không phải UUID hợp lệ.
    # Giải pháp: để Qdrant tự sinh UUID, còn chunk_id giữ trong payload
    # để hierarchy lookup (parent_id, children_ids) vẫn hoạt động.
    # ----------------------------------------------------------------
    logger.info(f"Upserting {len(all_chunk_dicts)} chunks to Qdrant...")

    payloads = [
        {"content": cd["content"], **cd["metadata"]}
        for cd in all_chunk_dicts
    ]

    # ids=None → Qdrant auto-generates UUIDs
    await qdrant.upsert_vectors(
        collection_name=settings.qdrant_legal_collection,
        vectors=all_embeddings,
        payloads=payloads,
    )

    # Verify
    final_count = await qdrant.count_points(settings.qdrant_legal_collection)
    logger.info(f"Indexing complete. Total documents: {final_count}")

    await qdrant.close()


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Index legal documents")
    parser.add_argument(
        "--dir",
        type=Path,
        default=settings.documents_dir,
        help="Documents directory",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Embedding batch size",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-indexing",
    )

    args = parser.parse_args()

    await index_documents(
        documents_dir=args.dir,
        batch_size=args.batch_size,
        force_reindex=args.force,
    )


if __name__ == "__main__":
    asyncio.run(main())
