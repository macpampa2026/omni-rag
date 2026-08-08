"""Servicio de recuperación: pregunta -> fragmentos más relevantes."""
from __future__ import annotations

from app.services.ollama_client import OllamaClient
from app.services.vector_store import Chunk, VectorStore


def retrieve(
    store: VectorStore, ollama: OllamaClient, question: str, k: int
) -> list[Chunk]:
    query_vec = ollama.embed_one(question)
    return store.search(query_vec, k)
