"""Dataset loader for RAGAS evaluation golden dataset.

Supports loading from JSON (golden_dataset.json) and Excel (.xlsx) files.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class GoldenSample:
    """A single ground-truth QA sample for evaluation."""

    id: str
    question: str
    ground_truth: str
    category: str = "general"
    keywords: list[str] = field(default_factory=list)


class DatasetLoader:
    """Load and manage the golden evaluation dataset."""

    def load(self, path: str) -> list[GoldenSample]:
        """Load samples from a .json or .xlsx file.

        Args:
            path: Path to golden_dataset.json or .xlsx file.

        Returns:
            List of GoldenSample objects.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file format is unsupported or malformed.
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Dataset file not found: {path}")

        suffix = p.suffix.lower()
        if suffix == ".json":
            return self._load_json(p)
        elif suffix in (".xlsx", ".xls"):
            return self._load_excel(p)
        else:
            raise ValueError(f"Unsupported file format: {suffix}. Use .json or .xlsx")

    def filter_by_category(
        self,
        samples: list[GoldenSample],
        category: Optional[str],
    ) -> list[GoldenSample]:
        """Filter samples by category.

        Args:
            samples: Full list of samples.
            category: Category to filter on, or None to return all.

        Returns:
            Filtered list.
        """
        if not category:
            return samples
        filtered = [s for s in samples if s.category == category]
        logger.info(f"Filtered to category '{category}': {len(filtered)} samples")
        return filtered

    def _load_json(self, path: Path) -> list[GoldenSample]:
        """Load from golden_dataset.json format."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        raw_samples = data.get("samples", [])
        if not raw_samples:
            raise ValueError(f"No samples found in {path}")

        samples = []
        for i, item in enumerate(raw_samples):
            if not item.get("question") or not item.get("ground_truth"):
                logger.warning(f"Skipping sample {i}: missing question or ground_truth")
                continue
            samples.append(
                GoldenSample(
                    id=item.get("id", f"sample_{i:03d}"),
                    category=item.get("category", "general"),
                    question=item["question"],
                    ground_truth=item["ground_truth"],
                    keywords=item.get("keywords", []),
                )
            )

        logger.info(f"Loaded {len(samples)} samples from {path}")
        return samples

    def _load_excel(self, path: Path) -> list[GoldenSample]:
        """Load from Excel format with columns: question, ground_truth, category."""
        try:
            import pandas as pd
        except ImportError as e:
            raise ImportError("pandas is required to load Excel files: pip install pandas openpyxl") from e

        df = pd.read_excel(path, engine="openpyxl")

        required_cols = {"question", "ground_truth"}
        missing = required_cols - set(df.columns.str.lower())
        if missing:
            raise ValueError(f"Excel missing required columns: {missing}")

        # Normalize column names
        df.columns = df.columns.str.lower().str.strip()

        samples = []
        for i, row in df.iterrows():
            question = str(row.get("question", "")).strip()
            ground_truth = str(row.get("ground_truth", "")).strip()
            if not question or not ground_truth:
                continue
            category = str(row.get("category", "general")).strip()
            keywords_raw = str(row.get("keywords", "")).strip()
            keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]

            samples.append(
                GoldenSample(
                    id=f"rag_{(i + 1):03d}",
                    category=category,
                    question=question,
                    ground_truth=ground_truth,
                    keywords=keywords,
                )
            )

        logger.info(f"Loaded {len(samples)} samples from Excel {path}")
        return samples
