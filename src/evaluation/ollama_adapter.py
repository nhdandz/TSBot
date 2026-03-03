"""vLLM + HuggingFace adapter cho RAGAS evaluation.

Dùng vLLM (OpenAI-compatible) thay Ollama cho judge LLM,
dùng HuggingFaceEmbeddings (sentence-transformers) cho embeddings.
"""

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI

from src.core.config import EvalSettings


def get_ragas_llm(config: EvalSettings) -> ChatOpenAI:
    """LLM instance cho RAGAS judge — dùng vLLM trên A100."""
    return ChatOpenAI(
        base_url=config.vllm_base_url,
        api_key=config.vllm_api_key,
        model=config.eval_judge_model,
        temperature=0,
    )


def get_ragas_embeddings(config: EvalSettings) -> HuggingFaceEmbeddings:
    """Embeddings cho RAGAS metrics — dùng sentence-transformers local."""
    return HuggingFaceEmbeddings(
        model_name=config.eval_embedding_model,
        model_kwargs={"device": "cuda"},
        encode_kwargs={"normalize_embeddings": True},
    )
