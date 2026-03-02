"""Convert Excel dataset to golden_dataset.json format.

Usage:
    python scripts/import_dataset_from_excel.py --input data/my_dataset.xlsx
    python scripts/import_dataset_from_excel.py --input data/my_dataset.xlsx --output data/evaluation/golden_dataset.json
    python scripts/import_dataset_from_excel.py --input data/my_dataset.xlsx --preview

Excel format (required columns):
    - question     : Câu hỏi
    - ground_truth : Câu trả lời chuẩn
    - category     : (optional) Danh mục, vd: suc_khoe, dieu_kien, ho_so...
    - keywords     : (optional) Từ khóa, phân cách bằng dấu phẩy

Example Excel header:
    question | ground_truth | category | keywords
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def convert_excel_to_json(
    input_path: str,
    output_path: str,
    preview: bool = False,
) -> None:
    """Convert Excel file to golden_dataset.json.

    Args:
        input_path: Path to input .xlsx file.
        output_path: Path for output .json file.
        preview: If True, print preview without saving.
    """
    try:
        import pandas as pd
    except ImportError:
        print("ERROR: pandas is required. Install with: pip install pandas openpyxl")
        sys.exit(1)

    input_path = Path(input_path)
    if not input_path.exists():
        print(f"ERROR: File not found: {input_path}")
        sys.exit(1)

    print(f"Reading: {input_path}")

    try:
        df = pd.read_excel(input_path, engine="openpyxl")
    except Exception as e:
        print(f"ERROR: Could not read Excel file: {e}")
        sys.exit(1)

    # Normalize column names
    df.columns = df.columns.str.lower().str.strip()

    print(f"Columns found: {list(df.columns)}")
    print(f"Total rows: {len(df)}")

    # Validate required columns
    required_cols = {"question", "ground_truth"}
    missing = required_cols - set(df.columns)
    if missing:
        print(f"ERROR: Missing required columns: {missing}")
        print("Required columns: question, ground_truth")
        print("Optional columns: category, keywords")
        sys.exit(1)

    # Build samples
    samples = []
    skipped = 0
    for i, row in df.iterrows():
        question = str(row.get("question", "")).strip()
        ground_truth = str(row.get("ground_truth", "")).strip()

        if not question or question == "nan" or not ground_truth or ground_truth == "nan":
            skipped += 1
            continue

        category = str(row.get("category", "general")).strip()
        if category == "nan" or not category:
            category = "general"

        keywords_raw = str(row.get("keywords", "")).strip()
        if keywords_raw == "nan":
            keywords_raw = ""
        keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]

        samples.append({
            "id": f"rag_{(len(samples) + 1):03d}",
            "category": category,
            "question": question,
            "ground_truth": ground_truth,
            "keywords": keywords,
        })

    print(f"\nConverted: {len(samples)} samples")
    if skipped > 0:
        print(f"Skipped (empty rows): {skipped}")

    if preview:
        print("\n--- PREVIEW (first 3 samples) ---")
        for s in samples[:3]:
            print(f"\nID: {s['id']}")
            print(f"Category: {s['category']}")
            print(f"Question: {s['question'][:100]}...")
            print(f"Ground truth: {s['ground_truth'][:100]}...")
            print(f"Keywords: {s['keywords']}")
        print("\n(Preview mode - not saving)")
        return

    # Save output
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Merge with existing if file exists
    if output_path.exists():
        print(f"\nExisting file found: {output_path}")
        choice = input("Overwrite (o) or merge/append (m)? [o/m]: ").strip().lower()
        if choice == "m":
            with open(output_path, encoding="utf-8") as f:
                existing = json.load(f)
            existing_ids = {s["id"] for s in existing.get("samples", [])}
            # Re-index new samples to avoid ID conflicts
            new_samples = []
            counter = len(existing.get("samples", [])) + 1
            for s in samples:
                s["id"] = f"rag_{counter:03d}"
                counter += 1
                new_samples.append(s)
            samples = existing.get("samples", []) + new_samples
            print(f"Merged: total {len(samples)} samples")

    output = {
        "version": "1.0",
        "description": "Golden dataset cho đánh giá RAG pipeline TSBot",
        "samples": samples,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to: {output_path}")
    print("Done!")


def main():
    parser = argparse.ArgumentParser(
        description="Convert Excel dataset to golden_dataset.json for RAGAS evaluation"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to input .xlsx file",
    )
    parser.add_argument(
        "--output",
        default="data/evaluation/golden_dataset.json",
        help="Path to output .json file (default: data/evaluation/golden_dataset.json)",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview first 3 samples without saving",
    )
    args = parser.parse_args()

    convert_excel_to_json(
        input_path=args.input,
        output_path=args.output,
        preview=args.preview,
    )


if __name__ == "__main__":
    main()
