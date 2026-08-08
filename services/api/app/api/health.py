"""Endpoints de salud: liveness (/health) y readiness (/health/ready)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_ollama, get_settings, get_store
from app.config import Settings
from app.models.schemas import HealthResponse, ReadyResponse
from app.services.ollama_client import OllamaClient
from app.services.vector_store import VectorStore

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Liveness")
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """El proceso está vivo (no comprueba dependencias externas)."""
    return HealthResponse(app=settings.app_name, version=settings.version)


@router.get("/health/ready", response_model=ReadyResponse, summary="Readiness")
def ready(
    settings: Settings = Depends(get_settings),
    ollama: OllamaClient = Depends(get_ollama),
    store: VectorStore = Depends(get_store),
) -> ReadyResponse:
    """Listo para servir: comprueba que Ollama responde y reporta el índice."""
    ollama_ok = ollama.ping()
    return ReadyResponse(
        status="ready" if ollama_ok else "degraded",
        ollama="up" if ollama_ok else "down",
        indexed_documents=len(store.list_documents()),
        indexed_chunks=store.count_chunks(),
    )
