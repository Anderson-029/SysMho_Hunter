"""
Configuración centralizada del CLI via pydantic-settings.
Lee variables del archivo .env (opcional) y del entorno.

Versión CLI: solo cerebro (Ollama/Gemini) y RAG (Qdrant).
Sin base de datos, sin JWT, sin servidor web.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Cerebro — API cloud (Nivel 3, fallback)
    gemini_api_key: str = ""

    # Cerebro — Ollama (Nivel 2, LLM local)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b-instruct-q6_K"

    # RAG — Qdrant + embeddings
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "security_knowledge"
    embedding_model: str = "nomic-embed-text"
    embedding_dimensions: int = 768

    # Operación
    debug: bool = False
    max_concurrent_tools: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
