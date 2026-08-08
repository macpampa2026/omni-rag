"""Punto de entrada de la aplicación FastAPI.

Arma la app, configura logging, crea los objetos de larga vida en el lifespan
(config, cliente Ollama, vector store) y monta los routers.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app import __version__
from app.api import ask, documents, health
from app.config import get_settings
from app.logging_conf import configure_logging
from app.services.ollama_client import OllamaClient, OllamaError
from app.services.vector_store import InMemoryVectorStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Respetamos cualquier estado ya inyectado (los tests pre-cargan dobles).
    settings = getattr(app.state, "settings", None) or get_settings()
    app.state.settings = settings
    configure_logging(settings.log_level)
    logger = logging.getLogger("app.startup")

    if not getattr(app.state, "ollama", None):
        app.state.ollama = OllamaClient(
            base_url=settings.ollama_url,
            embed_model=settings.embed_model,
            gen_model=settings.gen_model,
        )
    if not getattr(app.state, "store", None):
        if settings.database_url:
            from app.services.pgvector_store import PgVectorStore

            app.state.store = PgVectorStore(settings.database_url)
            app.state.store_backend = "postgres"
        else:
            app.state.store = InMemoryVectorStore(settings.index_path)
            app.state.store_backend = "memory"
    logger.info(
        "omni-rag iniciado",
        extra={
            "version": settings.version,
            "gen_model": settings.gen_model,
            "embed_model": settings.embed_model,
            "store_backend": getattr(app.state, "store_backend", "memory"),
        },
    )
    try:
        yield
    finally:
        app.state.ollama.close()
        logging.getLogger("app.shutdown").info("omni-rag detenido")


def create_app() -> FastAPI:
    app = FastAPI(
        title="omni-rag",
        version=__version__,
        summary="Plataforma de RAG para soporte y postventa retail.",
        description=(
            "Responde preguntas usando SOLO documentos indexados, con citas "
            "verificables y sin alucinar. Motor 100% local (Ollama)."
        ),
        lifespan=lifespan,
    )

    app.include_router(health.router)
    app.include_router(documents.router)
    app.include_router(ask.router)

    @app.exception_handler(OllamaError)
    async def _ollama_error_handler(_request, exc: OllamaError):
        return JSONResponse(
            status_code=503,
            content={"detail": f"Motor local no disponible: {exc}"},
        )

    @app.get("/", tags=["meta"], summary="Info de la API")
    def root() -> dict:
        return {
            "name": "omni-rag",
            "version": __version__,
            "docs": "/docs",
            "health": "/health",
        }

    return app


app = create_app()
