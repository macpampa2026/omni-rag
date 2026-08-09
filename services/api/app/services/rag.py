"""Servicio RAG: recupera contexto y genera una respuesta ANCLADA y citada.

El corazón anti-alucinación: el modelo responde SOLO con los fragmentos
recuperados, cita cada afirmación con [n], y si la respuesta no está en el
contexto lo dice explícitamente en vez de inventar.
"""
from __future__ import annotations

from app.models.schemas import AskResponse, Source
from app.services.ollama_client import OllamaClient
from app.services.rerank import rerank
from app.services.retrieval import retrieve
from app.services.vector_store import Chunk, VectorStore

FALLBACK = "La información disponible no cubre ese punto."

SYSTEM_PROMPT = (
    "Sos un asistente de soporte y postventa. Respondés en español, con "
    "precisión y tono profesional y cordial.\n"
    "REGLAS ESTRICTAS:\n"
    "1) Respondé ÚNICAMENTE con información del CONTEXTO entregado. No uses "
    "conocimiento externo ni inventes datos, precios, plazos ni pasos.\n"
    f"2) Si la respuesta no está en el contexto, respondé exactamente: "
    f"'{FALLBACK}' y no agregues nada más.\n"
    "3) Citá SIEMPRE la fuente con el número entre corchetes, por ejemplo [1]. "
    "Cada afirmación relevante debe terminar con su cita [n].\n"
    "4) Sé claro y breve; usá viñetas cuando ayude. No más de ~8 viñetas o "
    "200 palabras.\n"
    "5) No inventes números ni expandas siglas que no estén textualmente en "
    "el contexto."
)


def _build_context(hits: list[Chunk]) -> str:
    parts: list[str] = []
    for i, hit in enumerate(hits, start=1):
        loc = f", p. {hit.page}" if hit.page is not None else ""
        parts.append(f"[{i}] (fuente: {hit.title}{loc})\n{hit.text}")
    return "\n\n".join(parts)


def _excerpt(text: str, limit: int = 220) -> str:
    return text[:limit] + ("..." if len(text) > limit else "")


def answer(
    store: VectorStore,
    ollama: OllamaClient,
    *,
    question: str,
    k: int,
    temperature: float,
    num_predict: int,
    gen_model: str,
    rerank_enabled: bool = False,
    rerank_candidates: int = 20,
) -> AskResponse:
    # Con reranking: recuperamos un pool grande por similitud y lo reordenamos
    # con el LLM; si no, recuperamos directamente los top-k.
    if rerank_enabled and rerank_candidates > k:
        candidates = retrieve(store, ollama, question, rerank_candidates)
        hits = rerank(ollama, question, candidates, k)
    else:
        hits = retrieve(store, ollama, question, k)

    if not hits:
        return AskResponse(
            question=question, answer=FALLBACK, sources=[], model=gen_model
        )

    context = _build_context(hits)
    user_msg = f"CONTEXTO:\n{context}\n\nPREGUNTA: {question}"
    text = ollama.chat(
        SYSTEM_PROMPT,
        user_msg,
        temperature=temperature,
        num_predict=num_predict,
    )

    sources = [
        Source(
            n=i,
            doc_id=hit.doc_id,
            title=hit.title,
            page=hit.page,
            score=round(hit.score, 4),
            excerpt=_excerpt(hit.text),
        )
        for i, hit in enumerate(hits, start=1)
    ]
    return AskResponse(
        question=question, answer=text, sources=sources, model=gen_model
    )
