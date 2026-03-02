"""CLI entry point for RAGAS evaluation pipeline.

Usage:
    # Chạy toàn bộ dataset
    python scripts/run_evaluation.py

    # Chỉ chạy category sức khỏe
    python scripts/run_evaluation.py --category suc_khoe

    # Chỉ chạy 5 câu đầu (debug nhanh)
    python scripts/run_evaluation.py --limit 5

    # Chọn subset metrics (không cần ground_truth cho 2 metrics đầu)
    python scripts/run_evaluation.py --metrics faithfulness,answer_relevancy

    # Chỉ định dataset và output directory
    python scripts/run_evaluation.py --dataset data/evaluation/golden_dataset.json --output-dir data/evaluation/results

    # Quick smoke test (3 samples, 2 metrics nhanh)
    python scripts/run_evaluation.py --limit 3 --metrics faithfulness,answer_relevancy
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("run_evaluation")

VALID_METRICS = {"faithfulness", "answer_relevancy", "context_precision", "context_recall"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run RAGAS evaluation for TSBot RAG pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dataset",
        default=None,
        help="Path to golden_dataset.json or .xlsx (default: from EvalSettings)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory to save results (default: from EvalSettings)",
    )
    parser.add_argument(
        "--category",
        default=None,
        help="Filter by category (e.g. suc_khoe, dieu_kien, ho_so)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of samples (useful for quick test)",
    )
    parser.add_argument(
        "--metrics",
        default=None,
        help=(
            "Comma-separated list of metrics to run. "
            f"Valid: {', '.join(sorted(VALID_METRICS))}. "
            "Default: all 4 metrics."
        ),
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Number of samples to query in parallel (default: from EvalSettings)",
    )
    parser.add_argument(
        "--no-json",
        action="store_true",
        help="Skip saving JSON report",
    )
    parser.add_argument(
        "--no-markdown",
        action="store_true",
        help="Skip saving Markdown report",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    # --- Parse metrics ---
    selected_metrics = None
    if args.metrics:
        selected_metrics = [m.strip() for m in args.metrics.split(",")]
        invalid = set(selected_metrics) - VALID_METRICS
        if invalid:
            logger.error(f"Invalid metrics: {invalid}. Valid: {VALID_METRICS}")
            sys.exit(1)
        logger.info(f"Using metrics: {selected_metrics}")

    # --- Load config ---
    from src.core.config import get_eval_settings
    config = get_eval_settings()

    dataset_path = args.dataset or config.eval_dataset_path
    output_dir = args.output_dir or config.eval_results_dir

    # --- Check RAGAS is installed ---
    try:
        import ragas  # noqa: F401
    except ImportError:
        logger.error(
            "ragas is not installed. Run: uv pip install -e '.[eval]'"
        )
        sys.exit(1)

    # --- Load dataset ---
    from src.evaluation.dataset_loader import DatasetLoader
    loader = DatasetLoader()

    logger.info(f"Loading dataset from: {dataset_path}")
    try:
        samples = loader.load(dataset_path)
    except FileNotFoundError:
        logger.error(f"Dataset not found: {dataset_path}")
        logger.error(
            "Create it with: python scripts/import_dataset_from_excel.py --input your_file.xlsx"
        )
        sys.exit(1)

    # --- Filter by category ---
    if args.category:
        samples = loader.filter_by_category(samples, args.category)
        if not samples:
            logger.error(f"No samples found for category: {args.category}")
            sys.exit(1)

    # --- Limit samples ---
    if args.limit:
        samples = samples[: args.limit]
        logger.info(f"Limited to {len(samples)} samples")

    logger.info(f"Evaluating {len(samples)} samples")

    # --- Initialize RAG Agent ---
    logger.info("Initializing RAG Agent...")
    try:
        from src.agents.rag_agent import get_rag_agent
        rag_agent = get_rag_agent()
    except Exception as e:
        logger.error(f"Failed to initialize RAG Agent: {e}")
        logger.error("Make sure Qdrant and Ollama are running.")
        sys.exit(1)

    # --- Initialize Evaluator ---
    from src.evaluation.evaluator import RAGEvaluator
    evaluator = RAGEvaluator(
        rag_agent=rag_agent,
        config=config,
        metrics=selected_metrics,
    )

    # --- Run Evaluation ---
    logger.info("Starting RAGAS evaluation...")
    try:
        result = await evaluator.run(
            samples=samples,
            batch_size=args.batch_size,
        )
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        sys.exit(1)

    # --- Print Summary ---
    from src.evaluation.reporter import EvaluationReporter
    reporter = EvaluationReporter()
    reporter.print_summary(result)

    # --- Save Reports ---
    if not args.no_json:
        json_path = reporter.save_json(result, output_dir)
        print(f"JSON report: {json_path}")

    if not args.no_markdown:
        md_path = reporter.save_markdown(result, output_dir)
        print(f"Markdown report: {md_path}")

    # --- Exit code based on failed samples ---
    if result.failed_samples > 0:
        pct_failed = result.failed_samples / result.total_samples * 100
        logger.warning(f"{result.failed_samples}/{result.total_samples} samples failed ({pct_failed:.0f}%)")
        if pct_failed > 50:
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
