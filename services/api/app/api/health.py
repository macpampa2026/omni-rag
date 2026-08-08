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
    """Listo para servir: comprueba Ollama y el almacén, y reporta el índice."""
    ollama_ok = ollama.ping()
    backend = "postgres" if store.__class__.__name__ == "PgVectorStore" else "memory"
    try:
        docs = len(store.list_documents())
        chunks = store.count_chunks()
        store_ok = True
    except Exception:  # noqa: BLE001
        docs, chunks, store_ok = 0, 0, False
    healthy = ollama_ok and store_ok
    return ReadyResponse(
        status="ready" if healthy else "degraded",
        ollama="up" if ollama_ok else "down",
        store=f"{backend}:{'up' if store_ok else 'down'}",
        indexed_documents=docs,
        indexed_chunks=chunks,
    )
