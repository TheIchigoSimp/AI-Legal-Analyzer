"""
Centralized application configuration.
All settings are driven by environment variables (loaded from .env file).
"""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # LLM (Groq)
    groq_api_key: str
    llm_model: str = "llama-3.3-70b-versatile"

    # Embeddings (local HuggingFace)
    embedding_model: str = "all_MiniLM-L6-v2"

    # JWT Auth
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Storage Paths
    database_path: str = "data/legal_analyzer.db"
    faiss_index_path: str = "data/faiss_index"
    upload_dir: str = "uploads"

    # Logging
    log_level: str = "INFO"

    @property
    def database_dir(self) -> Path:
        return Path(self.database_path).parent


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton of application settings."""
    return Settings()
