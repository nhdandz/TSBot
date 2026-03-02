"""Evaluation reporter: outputs JSON and Markdown reports."""

import json
import logging
from datetime import datetime
from pathlib import Path

from src.evaluation.evaluator import EvaluationResult, SampleResult

logger = logging.getLogger(__name__)

METRIC_LABELS = {
    "faithfulness": "Faithfulness (chống hallucination)",
    "answer_relevancy": "Answer Relevancy (trả lời đúng câu hỏi)",
    "context_precision": "Context Precision (context relevant)",
    "context_recall": "Context Recall (ground truth được cover)",
}


class EvaluationReporter:
    """Format and save evaluation results as JSON and Markdown."""

    def save_json(self, result: EvaluationResult, output_dir: str) -> Path:
        """Save full result as JSON.

        Args:
            result: EvaluationResult object.
            output_dir: Directory to save into.

        Returns:
            Path to saved file.
        """
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = out_dir / f"results_{timestamp}.json"

        data = {
            "timestamp": timestamp,
            "total_samples": result.total_samples,
            "failed_samples": result.failed_samples,
            "config": result.config,
            "metrics_summary": result.metrics_summary,
            "sample_results": [
                {
                    "id": r.sample_id,
                    "question": r.question,
                    "ground_truth": r.ground_truth,
                    "answer": r.answer,
                    "retrieved_contexts_count": len(r.retrieved_contexts),
                    "faithfulness": r.faithfulness,
                    "answer_relevancy": r.answer_relevancy,
                    "context_precision": r.context_precision,
                    "context_recall": r.context_recall,
                    "error": r.error,
                }
                for r in result.sample_results
            ],
        }

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"[Reporter] JSON saved: {out_path}")
        return out_path

    def save_markdown(self, result: EvaluationResult, output_dir: str) -> Path:
        """Save human-readable Markdown report.

        Args:
            result: EvaluationResult object.
            output_dir: Directory to save into.

        Returns:
            Path to saved file.
        """
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = out_dir / f"report_{timestamp}.md"

        lines = self._build_markdown(result, timestamp)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info(f"[Reporter] Markdown saved: {out_path}")
        return out_path

    def print_summary(self, result: EvaluationResult) -> None:
        """Print summary table to console."""
        print("\n" + "=" * 60)
        print("  RAGAS EVALUATION SUMMARY")
        print("=" * 60)
        print(f"  Tổng samples: {result.total_samples}")
        print(f"  Samples thất bại: {result.failed_samples}")
        print(f"  Samples được đánh giá: {result.total_samples - result.failed_samples}")
        print()

        if result.metrics_summary:
            print(f"  {'Metric':<30} {'Mean':>8} {'±Std':>8} {'Min':>8} {'Max':>8}")
            print(f"  {'-'*30} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
            for metric, stats in result.metrics_summary.items():
                label = METRIC_LABELS.get(metric, metric)[:30]
                print(
                    f"  {label:<30} {stats['mean']:>8.4f} {stats['std']:>8.4f} "
                    f"{stats['min']:>8.4f} {stats['max']:>8.4f}"
                )
        else:
            print("  Không có metrics nào được tính.")

        print("=" * 60 + "\n")

    def _build_markdown(self, result: EvaluationResult, timestamp: str) -> list[str]:
        """Build lines for the Markdown report."""
        lines = [
            "# Báo cáo Đánh giá RAG Pipeline (RAGAS)",
            "",
            f"**Thời gian chạy:** {timestamp}",
            f"**Judge model:** {result.config.get('judge_model', 'N/A')}",
            f"**Embedding model:** {result.config.get('embedding_model', 'N/A')}",
            f"**Tổng samples:** {result.total_samples} | **Thất bại:** {result.failed_samples}",
            "",
            "---",
            "",
            "## 1. Tổng hợp Metrics",
            "",
            "| Metric | Ý nghĩa | Mean | ±Std | Min | Max |",
            "|--------|---------|------|------|-----|-----|",
        ]

        for metric, stats in result.metrics_summary.items():
            label = METRIC_LABELS.get(metric, metric)
            lines.append(
                f"| **{metric}** | {label} | {stats['mean']:.4f} | {stats['std']:.4f} "
                f"| {stats['min']:.4f} | {stats['max']:.4f} |"
            )

        # Category breakdown
        categories = {}
        for r in result.sample_results:
            # category not stored in SampleResult, will use id prefix or "all"
            pass

        lines += [
            "",
            "---",
            "",
            "## 2. Samples điểm thấp nhất",
            "",
        ]

        # Find lowest scoring samples (by faithfulness or first available metric)
        scored = [
            r for r in result.sample_results
            if r.faithfulness is not None or r.answer_relevancy is not None
        ]
        if scored:
            def _avg_score(r: SampleResult) -> float:
                vals = [
                    v for v in [r.faithfulness, r.answer_relevancy, r.context_precision, r.context_recall]
                    if v is not None
                ]
                return sum(vals) / len(vals) if vals else 0.0

            scored.sort(key=_avg_score)
            worst = scored[:5]

            lines.append("| ID | Question | F | AR | CP | CR |")
            lines.append("|-----|---------|---|----|----|-----|")
            for r in worst:
                q = r.question[:60] + "..." if len(r.question) > 60 else r.question
                f_str = f"{r.faithfulness:.2f}" if r.faithfulness is not None else "-"
                ar_str = f"{r.answer_relevancy:.2f}" if r.answer_relevancy is not None else "-"
                cp_str = f"{r.context_precision:.2f}" if r.context_precision is not None else "-"
                cr_str = f"{r.context_recall:.2f}" if r.context_recall is not None else "-"
                lines.append(f"| {r.sample_id} | {q} | {f_str} | {ar_str} | {cp_str} | {cr_str} |")
        else:
            lines.append("_Không có samples nào được chấm điểm._")

        lines += [
            "",
            "---",
            "",
            "## 3. Chú thích Metrics",
            "",
            "| Metric | Mô tả | Cần ground_truth? |",
            "|--------|-------|-------------------|",
            "| **Faithfulness** | Câu trả lời có bịa thông tin không có trong context không | Không |",
            "| **AnswerRelevancy** | Câu trả lời có thực sự trả lời câu hỏi không | Không |",
            "| **ContextPrecision** | Bao nhiêu context retrieve là thực sự relevant | Có |",
            "| **ContextRecall** | Ground truth có được cover bởi context không | Có |",
            "",
            "> Điểm từ 0-1, cao hơn là tốt hơn.",
        ]

        return lines
