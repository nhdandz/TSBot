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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_text_file(file_path: Path) -> str:
    """Read text from various file formats."""
    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        return file_path.read_text(encoding="utf-8")

    elif suffix == ".docx":
        try:
            from docx import Document

            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except ImportError:
            logger.warning("python-docx not installed, skipping .docx files")
            return ""

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


async def index_documents(
    documents_dir: Path,
    batch_size: int = 32,
    force_reindex: bool = False,
):
    """Index documents from directory into Qdrant.

    Args:
        documents_dir: Directory containing documents.
        batch_size: Batch size for embedding.
        force_reindex: Force re-indexing even if already exists.
    """
    logger.info(f"Indexing documents from: {documents_dir}")

    # Initialize services
    embedding_service = get_embedding_service()
    qdrant = get_qdrant_db()
    chunker = LegalDocumentChunker(
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

    # Process each document
    all_chunks = []
    all_embeddings = []

    for doc_path in document_files:
        logger.info(f"Processing: {doc_path.name}")

        # Read document
        text = read_text_file(doc_path)
        if not text.strip():
            logger.warning(f"Empty or unreadable: {doc_path.name}")
            continue

        # Chunk document
        doc_metadata = {
            "source": doc_path.name,
            "file_path": str(doc_path),
        }

        chunks = chunker.chunk_document(text, doc_metadata)
        logger.info(f"  Created {len(chunks)} chunks")

        # Embed chunks in batches
        chunk_texts = [c.content for c in chunks]

        for i in range(0, len(chunk_texts), batch_size):
            batch = chunk_texts[i:i + batch_size]
            batch_embeddings = embedding_service.encode_documents(batch)

            for j, embedding in enumerate(batch_embeddings):
                chunk_idx = i + j
                all_chunks.append(chunks[chunk_idx])
                all_embeddings.append(embedding.tolist())

    if not all_chunks:
        logger.warning("No chunks to index")
        return

    # Upsert to Qdrant
    logger.info(f"Upserting {len(all_chunks)} chunks to Qdrant...")

    payloads = []
    for chunk in all_chunks:
        payload = {
            "content": chunk.content,
            **chunk.metadata,
        }
        payloads.append(payload)

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
