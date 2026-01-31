"""Script to process and prepare legal documents for indexing."""

import asyncio
import json
import logging
import re
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
from src.utils.chunking import LegalDocumentChunker
from src.utils.vietnamese import VietnameseTextProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_document_metadata(text: str) -> dict:
    """Extract metadata from document header.

    Args:
        text: Document text.

    Returns:
        Extracted metadata.
    """
    metadata = {}

    # Try to extract document number (Số: 123/QĐ-BQP)
    doc_number_match = re.search(
        r"Số[:\s]+(\d+/[A-Z\-]+)",
        text[:1000],
        re.IGNORECASE,
    )
    if doc_number_match:
        metadata["document_number"] = doc_number_match.group(1)

    # Try to extract document type
    doc_types = [
        ("thông tư", "thong_tu"),
        ("quyết định", "quyet_dinh"),
        ("nghị định", "nghi_dinh"),
        ("hướng dẫn", "huong_dan"),
        ("quy chế", "quy_che"),
        ("quy định", "quy_dinh"),
    ]

    text_lower = text[:2000].lower()
    for vn_type, type_code in doc_types:
        if vn_type in text_lower:
            metadata["document_type"] = type_code
            break

    # Try to extract issuing authority
    authorities = [
        ("bộ quốc phòng", "BQP"),
        ("bộ công an", "BCA"),
        ("bộ giáo dục", "BGDDT"),
        ("chính phủ", "CP"),
    ]

    for vn_auth, auth_code in authorities:
        if vn_auth in text_lower:
            metadata["issuing_authority"] = auth_code
            break

    # Try to extract year
    year_match = re.search(r"\b(20[12][0-9])\b", text[:1000])
    if year_match:
        metadata["year"] = int(year_match.group(1))

    return metadata


def clean_document_text(text: str) -> str:
    """Clean and normalize document text.

    Args:
        text: Raw document text.

    Returns:
        Cleaned text.
    """
    # Remove excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    # Remove page numbers
    text = re.sub(r"\n\s*\d+\s*\n", "\n", text)

    # Normalize dashes
    text = text.replace("–", "-").replace("—", "-")

    # Fix common OCR errors in Vietnamese
    ocr_fixes = {
        "đ ": "đ",
        " đ": "đ",
        "Đ ": "Đ",
        " Đ": "Đ",
    }
    for wrong, right in ocr_fixes.items():
        text = text.replace(wrong, right)

    return text.strip()


def analyze_document_structure(text: str) -> dict:
    """Analyze document structure and extract statistics.

    Args:
        text: Document text.

    Returns:
        Structure analysis.
    """
    analysis = {
        "total_chars": len(text),
        "chapters": 0,
        "articles": 0,
        "clauses": 0,
    }

    # Count chapters
    analysis["chapters"] = len(re.findall(
        r"^(?:CHƯƠNG|Chương)\s+[IVXLCDM\d]+",
        text,
        re.MULTILINE | re.IGNORECASE,
    ))

    # Count articles
    analysis["articles"] = len(re.findall(
        r"^(?:ĐIỀU|Điều)\s+\d+",
        text,
        re.MULTILINE | re.IGNORECASE,
    ))

    # Estimate clauses (lines starting with number.)
    analysis["clauses"] = len(re.findall(
        r"^\d+\.\s+",
        text,
        re.MULTILINE,
    ))

    return analysis


def process_document(file_path: Path, output_dir: Path) -> dict:
    """Process a single document.

    Args:
        file_path: Path to input document.
        output_dir: Directory for processed output.

    Returns:
        Processing result.
    """
    logger.info(f"Processing: {file_path.name}")

    # Read file
    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        text = file_path.read_text(encoding="utf-8")
    elif suffix == ".docx":
        try:
            from docx import Document

            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            logger.error(f"Failed to read .docx: {e}")
            return {"error": str(e)}
    elif suffix == ".pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(file_path)
            pages = [page.extract_text() for page in reader.pages]
            text = "\n".join(pages)
        except Exception as e:
            logger.error(f"Failed to read .pdf: {e}")
            return {"error": str(e)}
    else:
        return {"error": f"Unsupported format: {suffix}"}

    if not text.strip():
        return {"error": "Empty document"}

    # Clean text
    cleaned_text = clean_document_text(text)

    # Extract metadata
    metadata = extract_document_metadata(cleaned_text)
    metadata["source_file"] = file_path.name

    # Analyze structure
    structure = analyze_document_structure(cleaned_text)

    # Chunk document
    chunker = LegalDocumentChunker(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
    )
    chunks = chunker.chunk_document(cleaned_text, metadata)

    # Save processed output
    output_name = file_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save cleaned text
    (output_dir / f"{output_name}.txt").write_text(cleaned_text, encoding="utf-8")

    # Save chunks as JSON
    chunks_data = [
        {
            "content": chunk.content,
            "metadata": chunk.metadata,
            "hierarchy": chunker.get_hierarchy_path(chunk),
        }
        for chunk in chunks
    ]

    (output_dir / f"{output_name}_chunks.json").write_text(
        json.dumps(chunks_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    result = {
        "file": file_path.name,
        "metadata": metadata,
        "structure": structure,
        "chunks_count": len(chunks),
    }

    logger.info(f"  - {structure['articles']} articles, {len(chunks)} chunks")

    return result


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Process legal documents")
    parser.add_argument(
        "--input",
        type=Path,
        default=settings.documents_dir,
        help="Input documents directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=settings.documents_dir / "processed",
        help="Output directory for processed documents",
    )

    args = parser.parse_args()

    input_dir = args.input
    output_dir = args.output

    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        return

    # Find documents
    supported = {".txt", ".docx", ".pdf"}
    documents = [
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in supported
    ]

    if not documents:
        logger.warning(f"No documents found in {input_dir}")
        return

    logger.info(f"Found {len(documents)} documents")

    # Process each document
    results = []
    for doc_path in documents:
        result = process_document(doc_path, output_dir)
        results.append(result)

    # Save summary
    summary = {
        "total_documents": len(documents),
        "processed": len([r for r in results if "error" not in r]),
        "errors": len([r for r in results if "error" in r]),
        "total_chunks": sum(r.get("chunks_count", 0) for r in results),
        "results": results,
    }

    summary_path = output_dir / "processing_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    logger.info(f"\nProcessing complete:")
    logger.info(f"  - Documents processed: {summary['processed']}")
    logger.info(f"  - Errors: {summary['errors']}")
    logger.info(f"  - Total chunks: {summary['total_chunks']}")
    logger.info(f"  - Summary saved to: {summary_path}")


if __name__ == "__main__":
    main()
