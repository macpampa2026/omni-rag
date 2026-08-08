"""Dependencias de FastAPI: acceso a estado compartido y autenticación.

Los objetos de larga vida (config, cliente Ollama, vector store) viven en
``app.state`` y se crean una vez en el lifespan. Estas funciones los exponen
como dependencias inyectables en los handlers.
"""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Request, status

from app.config import Settings
from app.services.ollama_client import OllamaClient
from app.services.vector_store import VectorStore


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_ollama(request: Request) -> OllamaClient:
    return request.app.state.ollama


def get_store(request: Request) -> VectorStore:
    return request.app.state.store


def require_api_key(
    settings: Settings = Depends(get_settings),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    """Si hay una API key configurada, la exige en el header X-API-Key."""
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida o faltante (header X-API-Key).",
        )
