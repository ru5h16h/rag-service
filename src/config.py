from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Embedding
    embedding_backend: Literal["openai", "local"] = "local"
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_embedding_model: str = "text-embedding-3-small"
    local_embedding_model: str = "BAAI/bge-m3"
    embed_batch_size: int = 256
    embed_max_concurrency: int = 10

    # Chunking
    chunker_strategy: Literal["fixed", "semantic"] = "fixed"
    chunk_size_tokens: int = 512
    chunk_overlap_pct: float = 0.15

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "rag_chunks"

    # Postgres
    pg_dsn: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rag"

    # Cleaning
    min_content_chars: int = 100
    target_language: str = "en"
    language_confidence_threshold: float = 0.9

    # Pipeline
    pipeline_concurrency: int = 4


settings = Settings()
