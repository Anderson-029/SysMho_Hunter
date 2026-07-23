"""
Configuración centralizada via pydantic-settings.
Lee variables del archivo .env automáticamente.
"""

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Base de datos
    db_host: str = "127.0.0.1"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = ""
    db_name: str = "sysmho_hunter"

    # APIs cloud
    gemini_api_key: str = ""

    # LLM local — API OpenAI-compatible (LM Studio, Ollama /v1, vLLM, …)
    local_llm_base_url: str = "http://localhost:1234/v1"
    local_llm_model: str = "local-model"
    local_llm_api_key: str = "lm-studio"

    # RAG — Qdrant + embeddings OpenAI-compatible
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "security_knowledge"
    embedding_base_url: str = ""
    embedding_model: str = "text-embedding-nomic-embed-text-v1.5"
    embedding_dimensions: int = 768

    # Backend
    # Localhost por defecto — cambiar en producción a 0.0.0.0
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    debug: bool = False

    # Seguridad — generar única clave en .env
    # ej: API_KEY=tu_clave_super_secreta_aqui
    api_key: str = ""
    secret_key: str = "cambiar_en_produccion"

    # JWT
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Frontend
    frontend_url: str = "http://localhost:5173"

    @model_validator(mode="after")
    def _default_embedding_base_url(self) -> "Settings":
        if not self.embedding_base_url.strip():
            self.embedding_base_url = self.local_llm_base_url.rstrip("/")
        else:
            self.embedding_base_url = self.embedding_base_url.rstrip("/")
        self.local_llm_base_url = self.local_llm_base_url.rstrip("/")
        return self

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_url_sync(self) -> str:
        """URL síncrona para Alembic."""
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
