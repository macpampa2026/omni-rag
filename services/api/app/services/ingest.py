"""Servicio de ingesta: texto -> fragmentos -> embeddings -> vector store."""
from __future__ import annotations

import logging

from app.services.chunking import chunk_text
from app.services.ollama_client import OllamaClient
from app.services.vector_store import Chunk, VectorStore

logger = logging.getLogger(__name__)

_EMBED_BATCH = 48


def ingest_text(
    store: VectorStore,
    ollama: OllamaClient,
    *,
    doc_id: str,
    title: str,
    text: str,
    chunk_chars: int,
    overlap: int,
    page: int | None = None,
) -> int:
    """Indexa un texto y devuelve la cantidad de fragmentos creados."""
    pieces = chunk_text(text, chunk_chars=chunk_chars, overlap=overlap)
    if not pieces:
        return 0

    chunks: list[Chunk] = []
    for start in range(0, len(pieces), _EMBED_BATCH):
        batch = pieces[start : start + _EMBED_BATCH]
        vecs = ollama.embed(batch)
        for piece, vec in zip(batch, vecs, strict=True):
            chunks.append(
                Chunk(
                    id=-1,  # lo asigna el store
                    doc_id=doc_id,
                    title=title or doc_id,
                    text=piece,
                    vec=vec,
                    page=page,
                )
            )

    store.add(chunks)
    logger.info(
        "documento indexado",
        extra={"doc_id": doc_id, "chunks": len(chunks)},
    )
    return len(chunks)
