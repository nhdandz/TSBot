"""Configuration management using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "TSBot"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    cors_origins: List[str] = Field(default=["http://localhost:3000", "http://localhost:8080"])

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            import json

            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "tsbot"
    postgres_password: str = "tsbot_secret_password"
    postgres_db: str = "tsbot_db"
    postgres_pool_size: int = 10
    postgres_max_overflow: int = 20

    @property
    def postgres_dsn(self) -> str:
        """PostgreSQL connection string for asyncpg."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def postgres_dsn_sync(self) -> str:
        """PostgreSQL connection string for sync operations."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_grpc_port: int = 6334
    qdrant_legal_collection: str = "legal_documents"
    qdrant_sql_examples_collection: str = "sql_examples"
    qdrant_intents_collection: str = "intents"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_main_model: str = "qwen2.5:7b-instruct"
    ollama_main_temperature: float = 0.1
    ollama_main_top_p: float = 0.9
    ollama_grader_model: str = "qwen2.5:1.5b"
    ollama_grader_temperature: float = 0.0

    # Embeddings
    embedding_model: str = "AITeamVN/Vietnamese_Embedding"
    embedding_fallback_model: str = "nomic-embed-text"
    embedding_dimension: int = 1024

    # RAG
    rag_chunk_size: int = 512
    rag_chunk_overlap: int = 50
    rag_top_k: int = 5
    rag_relevance_threshold: float = 0.7
    
    # Advanced RAG Features
    use_hybrid_search: bool = True
    use_semantic_cache: bool = True
    use_query_analysis: bool = True
    use_query_expansion: bool = True
    use_smart_retrieval: bool = True
    
    # Cache
    cache_similarity_threshold: float = 0.92
    cache_ttl_hours: int = 24
    
    # Reranker
    reranker_model: str = "namdp-ptit/ViRanker"
    reranker_top_k: int = 3
    # Weights: cross_encoder, retrieval, metadata
    reranker_weights: dict = {"cross_encoder": 0.55, "retrieval": 0.35, "metadata": 0.10}

    # SQL Agent
    sql_max_retries: int = 3
    sql_few_shot_examples: int = 5

    # Semantic Router
    router_similarity_threshold: float = 0.85
    router_faq_collection: str = "intents"

    # Authentication
    secret_key: str = "your-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    admin_username: str = "admin"
    admin_password: str = "admin123"

    # Paths
    data_dir: Path = Path("./data")
    documents_dir: Path = Path("./data/documents")
    sql_examples_dir: Path = Path("./data/sql_examples")
    intents_dir: Path = Path("./data/intents")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
