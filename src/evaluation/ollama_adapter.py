"""Ollama adapter for RAGAS evaluation.

Wraps ChatOllama + OllamaEmbeddings into RAGAS-compatible objects.
"""

from langchain_ollama import ChatOllama, OllamaEmbeddings

from src.core.config import EvalSettings


def get_ragas_llm(config: EvalSettings) -> ChatOllama:
    """Get ChatOllama instance configured for RAGAS judge."""
    return ChatOllama(
        model=config.eval_judge_model,
        base_url=config.ollama_base_url,
        temperature=0,
    )


def get_ragas_embeddings(config: EvalSettings) -> OllamaEmbeddings:
    """Get OllamaEmbeddings instance configured for RAGAS metrics."""
    return OllamaEmbeddings(
        model=config.eval_embedding_model,
        base_url=config.ollama_base_url,
    )
