"""Core configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

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

    # Environment
    environment: Literal["development", "staging", "production", "test"] = "development"

    # API
    api_version: str = "0.1.0"
    api_title: str = "Docuify API"
    api_prefix: str = "/api/v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # Security
    secret_key: str = Field(default="dev-secret-key-change-me-please-32chars", min_length=32)
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    # Rate Limiting
    rate_limit_enabled: bool = False
    rate_limit_times: int = 10
    rate_limit_seconds: int = 60

    # Database
    database_url: str = "sqlite+aiosqlite:///./dev.db"
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10
    auto_create_tables: bool = True

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Storage
    storage_dir: str = "./storage"
    max_upload_mb: int = 50
    max_download_mb: int = 100
    download_timeout_secs: int = 60
    allowed_url_schemes: str = "http,https"

    # Answer generation. "extractive" needs no model and no API key.
    llm_provider: Literal["extractive", "anthropic", "openai", "ollama"] = "extractive"
    llm_api_key: str | None = None
    llm_model: str | None = None
    llm_base_url: str | None = None  # OpenAI-compatible servers such as Ollama; operator only
    llm_temperature: float = 0.2
    llm_max_tokens: int = 1024
    allow_client_llm_keys: bool = True  # let a request bring its own key in X-LLM-Key

    # Dense embeddings. "none" = lexical (BM25) retrieval only.
    embedding_provider: Literal["none", "fastembed"] = "none"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # Retrieval
    rag_top_k: int = 5
    chunk_size: int = 900
    chunk_overlap: int = 150

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "console"] = "json"

    # Workers
    worker_broker_url: str | None = None
    worker_result_backend: str | None = None

    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL is a plain string."""
        return str(v)

    @field_validator("redis_url", mode="before")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        """Ensure Redis URL is a plain string."""
        return str(v)

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse allowed origins into a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def allowed_schemes_list(self) -> list[str]:
        """Parse allowed URL schemes into a list."""
        return [scheme.strip() for scheme in self.allowed_url_schemes.split(",")]

    @property
    def max_upload_bytes(self) -> int:
        """Convert max upload MB to bytes."""
        return self.max_upload_mb * 1024 * 1024

    @property
    def max_download_bytes(self) -> int:
        """Convert max download MB to bytes."""
        return self.max_download_mb * 1024 * 1024

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_test(self) -> bool:
        """Check if running in test mode."""
        return self.environment == "test"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
