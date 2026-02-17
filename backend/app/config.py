"""
Arthronyx — Application Configuration

All settings are loaded from environment variables with sensible defaults.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralized application settings loaded from environment."""

    # ── PostgreSQL ────────────────────────────────────────────
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "arthronyx"
    postgres_user: str = "arthronyx_user"
    postgres_password: str = "change_me_in_production"

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── Qdrant ────────────────────────────────────────────────
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "arthronyx_documents"

    # ── Neo4j ─────────────────────────────────────────────────
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "change_me_in_production"

    # ── PubMed ────────────────────────────────────────────────
    pubmed_api_key: str = ""
    pubmed_email: str = "your_email@example.com"

    # ── OpenAlex ──────────────────────────────────────────────
    openalex_api_key: str = ""

    # ── LLM ───────────────────────────────────────────────────
    # LLM Settings
    llm_api_key: str = ""
    llm_model: str = "llama3-8b-8192"
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_temperature: float = 0.0

    # ── Embedding ─────────────────────────────────────────────
    embedding_model: str = "BAAI/bge-large-en-v1.5"

    # ── Reranker ──────────────────────────────────────────────
    reranker_model: str = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"

    # ── Backend ───────────────────────────────────────────────
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_workers: int = 4
    log_level: str = "info"

    # ── Security ──────────────────────────────────────────────
    secret_key: str = "generate_a_secure_random_key_here"
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    # ── Retrieval Weights ─────────────────────────────────────
    weight_semantic: float = 0.5
    weight_evidence: float = 0.3
    weight_recency: float = 0.2

    # ── Retrieval Limits ──────────────────────────────────────
    bm25_top_k: int = 50
    dense_top_k: int = 50
    rerank_top_k: int = 20
    final_top_k: int = 10

    model_config = {"env_file": [".env", "../.env"], "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
