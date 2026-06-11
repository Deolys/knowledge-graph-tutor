"""Конфигурация приложения. Все env vars читаются здесь через pydantic-settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM — OpenAI-совместимый endpoint (httpx, без SDK). Сейчас Gemini.
    gemini_api_key: str = ""
    llm_model: str = "gemini-2.0-flash"
    llm_classifier_model: str = "gemini-2.0-flash"
    llm_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"

    # Database
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/kgtutor"
    )

    # Embeddings
    embeddings_model: str = "paraphrase-multilingual-MiniLM-L12-v2"

    # Ingestion
    confidence_threshold: float = 0.7
    merge_threshold: float = 0.85
    max_chapter_tokens: int = 4000

    # GraphRAG
    graphrag_max_entities: int = 15
    entity_link_threshold: float = 0.6

    # Test generation / progress
    questions_per_concept: int = 3
    learned_score_threshold: float = 0.7

    # Storage
    upload_dir: str = "uploads"


settings = Settings()
