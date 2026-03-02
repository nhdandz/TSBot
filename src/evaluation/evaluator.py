"""Core RAGAS evaluator for TSBot RAG pipeline.

Runs 4 metrics: Faithfulness, AnswerRelevancy, ContextPrecision, ContextRecall.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional

from src.core.config import EvalSettings, get_eval_settings
from src.evaluation.dataset_loader import GoldenSample
from src.evaluation.ollama_adapter import get_ragas_embeddings, get_ragas_llm

logger = logging.getLogger(__name__)


@dataclass
class SampleResult:
    """Evaluation result for a single sample."""

    sample_id: str
    question: str
    ground_truth: str
    answer: str
    retrieved_contexts: list[str]
    faithfulness: Optional[float] = None
    answer_relevancy: Optional[float] = None
    context_precision: Optional[float] = None
    context_recall: Optional[float] = None
    error: Optional[str] = None


@dataclass
class EvaluationResult:
    """Aggregated evaluation results across all samples."""

    sample_results: list[SampleResult] = field(default_factory=list)
    metrics_summary: dict = field(default_factory=dict)
    config: dict = field(default_factory=dict)
    total_samples: int = 0
    failed_samples: int = 0


class RAGEvaluator:
    """RAGAS-based evaluator for the TSBot RAG pipeline.

    Usage:
        evaluator = RAGEvaluator(rag_agent)
        result = await evaluator.run(samples)
    """

    AVAILABLE_METRICS = {
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
    }

    def __init__(
        self,
        rag_agent,
        config: Optional[EvalSettings] = None,
        metrics: Optional[list[str]] = None,
    ):
        """Initialize the evaluator.

        Args:
            rag_agent: RAGAgent instance with process_query() method.
            config: EvalSettings instance. Defaults to get_eval_settings().
            metrics: Subset of metrics to run. Defaults to all 4.
        """
        self.rag_agent = rag_agent
        self.config = config or get_eval_settings()
        self.selected_metrics = set(metrics) if metrics else self.AVAILABLE_METRICS

        self.llm = get_ragas_llm(self.config)
        self.embeddings = get_ragas_embeddings(self.config)

    def _build_metrics(self) -> list:
        """Build list of RAGAS metric objects based on selected_metrics."""
        try:
            from ragas.metrics import (
                AnswerRelevancy,
                ContextPrecision,
                ContextRecall,
                Faithfulness,
            )
        except ImportError as e:
            raise ImportError(
                "ragas is required. Install with: uv pip install -e '.[eval]'"
            ) from e

        metric_map = {
            "faithfulness": Faithfulness(),
            "answer_relevancy": AnswerRelevancy(),
            "context_precision": ContextPrecision(),
            "context_recall": ContextRecall(),
        }
        return [m for name, m in metric_map.items() if name in self.selected_metrics]

    async def _query_single(self, sample: GoldenSample) -> SampleResult:
        """Run RAG pipeline for one sample and return raw result."""
        try:
            rag_result = await self.rag_agent.process_query(sample.question)
            answer = rag_result.get("answer", "")
            sources = rag_result.get("sources", [])
            contexts = [s["content"] for s in sources if s.get("content")]
            return SampleResult(
                sample_id=sample.id,
                question=sample.question,
                ground_truth=sample.ground_truth,
                answer=answer,
                retrieved_contexts=contexts,
            )
        except Exception as exc:
            logger.error(f"[Eval] Failed to query sample {sample.id}: {exc}")
            return SampleResult(
                sample_id=sample.id,
                question=sample.question,
                ground_truth=sample.ground_truth,
                answer="",
                retrieved_contexts=[],
                error=str(exc),
            )

    async def run(
        self,
        samples: list[GoldenSample],
        batch_size: Optional[int] = None,
    ) -> EvaluationResult:
        """Run full evaluation pipeline.

        Args:
            samples: List of GoldenSample to evaluate.
            batch_size: Override eval_batch_size from config.

        Returns:
            EvaluationResult with per-sample and aggregated metrics.
        """
        if not samples:
            raise ValueError("No samples provided for evaluation")

        try:
            from ragas import evaluate
            from ragas.dataset_schema import EvaluationDataset, SingleTurnSample
        except ImportError as e:
            raise ImportError(
                "ragas is required. Install with: uv pip install -e '.[eval]'"
            ) from e

        bs = batch_size or self.config.eval_batch_size
        metrics = self._build_metrics()

        logger.info(
            f"[Eval] Starting evaluation: {len(samples)} samples, "
            f"metrics={[type(m).__name__ for m in metrics]}, "
            f"batch_size={bs}"
        )

        # Step 1: Run RAG pipeline for all samples (in batches)
        raw_results: list[SampleResult] = []
        for i in range(0, len(samples), bs):
            batch = samples[i : i + bs]
            batch_tasks = [self._query_single(s) for s in batch]
            batch_results = await asyncio.gather(*batch_tasks)
            raw_results.extend(batch_results)
            logger.info(f"[Eval] Queried {min(i + bs, len(samples))}/{len(samples)} samples")

        # Step 2: Build RAGAS EvaluationDataset (skip failed samples)
        ragas_samples = []
        valid_raw = []
        for r in raw_results:
            if r.error or not r.answer:
                logger.warning(f"[Eval] Skipping sample {r.sample_id}: {r.error or 'empty answer'}")
                continue
            ragas_samples.append(
                SingleTurnSample(
                    user_input=r.question,
                    response=r.answer,
                    retrieved_contexts=r.retrieved_contexts,
                    reference=r.ground_truth,
                )
            )
            valid_raw.append(r)

        if not ragas_samples:
            logger.error("[Eval] All samples failed, cannot evaluate")
            return EvaluationResult(
                sample_results=raw_results,
                total_samples=len(samples),
                failed_samples=len(samples),
            )

        # Step 3: RAGAS evaluate
        logger.info(f"[Eval] Running RAGAS evaluate on {len(ragas_samples)} valid samples...")
        dataset = EvaluationDataset(samples=ragas_samples)
        ragas_result = evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=self.llm,
            embeddings=self.embeddings,
        )

        # Step 4: Map per-sample scores back to SampleResult
        scores_df = ragas_result.to_pandas()
        metric_cols = [c for c in scores_df.columns if c not in ("user_input", "response", "reference")]

        for i, r in enumerate(valid_raw):
            if i < len(scores_df):
                row = scores_df.iloc[i]
                for col in metric_cols:
                    val = row.get(col)
                    col_clean = col.replace(" ", "_").lower()
                    if hasattr(r, col_clean):
                        setattr(r, col_clean, float(val) if val is not None else None)

        # Step 5: Build summary
        summary = {}
        for col in metric_cols:
            col_clean = col.replace(" ", "_").lower()
            vals = [
                getattr(r, col_clean)
                for r in valid_raw
                if getattr(r, col_clean, None) is not None
            ]
            if vals:
                import statistics
                summary[col_clean] = {
                    "mean": round(statistics.mean(vals), 4),
                    "std": round(statistics.stdev(vals), 4) if len(vals) > 1 else 0.0,
                    "min": round(min(vals), 4),
                    "max": round(max(vals), 4),
                    "count": len(vals),
                }

        eval_result = EvaluationResult(
            sample_results=raw_results,
            metrics_summary=summary,
            config={
                "judge_model": self.config.eval_judge_model,
                "embedding_model": self.config.eval_embedding_model,
                "ollama_base_url": self.config.ollama_base_url,
                "metrics": [type(m).__name__ for m in metrics],
            },
            total_samples=len(samples),
            failed_samples=len(raw_results) - len(valid_raw),
        )

        logger.info("[Eval] Evaluation complete. Summary:")
        for metric, stats in summary.items():
            logger.info(f"  {metric}: {stats['mean']:.4f} ± {stats['std']:.4f}")

        return eval_result
