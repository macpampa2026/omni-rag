"""Endpoint de consulta RAG: /ask."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_ollama, get_settings, get_store, require_api_key
from app.config import Settings
from app.models.schemas import AskRequest, AskResponse
from app.observability import metrics as obs
from app.services import rag
from app.services.ollama_client import OllamaClient
from app.services.vector_store import VectorStore

router = APIRouter(tags=["rag"], dependencies=[Depends(require_api_key)])


@router.post("/ask", response_model=AskResponse, summary="Preguntar (RAG)")
def ask(
    body: AskRequest,
    store: VectorStore = Depends(get_store),
    ollama: OllamaClient = Depends(get_ollama),
    settings: Settings = Depends(get_settings),
) -> AskResponse:
    obs.RAG_QUERIES.inc()
    k = body.top_k or settings.top_k
    return rag.answer(
        store,
        ollama,
        question=body.question,
        k=k,
        temperature=settings.gen_temperature,
        num_predict=settings.gen_num_predict,
        gen_model=settings.gen_model,
    )
