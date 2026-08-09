"""Configuración de la aplicación, cargada desde variables de entorno.

Usa pydantic-settings: cada campo puede sobrescribirse con una variable de
entorno con prefijo ``OMNIRAG_`` (o desde un archivo ``.env``).
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from app import __version__


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="OMNIRAG_", extra="ignore"
    )

    # --- Ollama ---
    ollama_url: str = "http://localhost:11434"
    embed_model: str = "nomic-embed-text"
    gen_model: str = "qwen2.5:7b"

    # --- Parámetros de RAG ---
    chunk_chars: int = 1000
    chunk_overlap: int = 150
    top_k: int = 8
    gen_temperature: float = 0.1
    gen_num_predict: int = 500

    # Reranking (opcional): recupera un pool más grande por similitud y lo
    # reordena con el LLM antes de quedarse con los top_k.
    rerank_enabled: bool = False
    rerank_candidates: int = 20

    # --- Almacenamiento ---
    index_path: str = "data/index.json"

    # --- Base de datos (M2) ---
    # Si se define, se usa PostgreSQL + pgvector en lugar del índice en memoria.
    # Ej: postgresql+psycopg://user:pass@host/db?sslmode=require
    database_url: str | None = None
    embed_dim: int = 768  # dimensión de los embeddings (nomic-embed-text = 768)

    # --- Cache (M4) ---
    # Opcional: si se define, cachea los embeddings de las consultas en Redis.
    # Ej: redis://localhost:6379/0
    redis_url: str | None = None

    # --- API ---
    app_name: str = "omni-rag"
    version: str = __version__
    api_key: str | None = None
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuración (cacheada: se lee una sola vez)."""
    return Settings()
