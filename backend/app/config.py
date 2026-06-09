"""Конфигурация приложения. Все env vars читаются здесь через pydantic-settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM (Google Gemini)
    gemini_api_key: str = ""
    model: str = "gemini-2.0-flash"

    # Database
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/kgtutor"
    )

    # Ingestion
    confidence_threshold: float = 0.7
    merge_threshold: float = 0.85
    embeddings_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    max_chapter_tokens: int = 4000

    # Test generation
    questions_per_concept: int = 3
    learned_score_threshold: float = 0.7

    # Storage
    upload_dir: str = "uploads"


settings = Settings()
