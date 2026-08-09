"""Reranking listwise con el LLM.

Recupera un pool de candidatos por similitud vectorial y le pide al LLM que los
reordene por relevancia a la pregunta, quedándose con los top-K. Es un paso
estándar en pipelines de RAG de calidad: mejora la precisión frente a usar solo
la distancia coseno. Una sola llamada al LLM (listwise), no una por candidato.
"""
from __future__ import annotations

import logging
import re

from app.services.ollama_client import OllamaClient
from app.services.vector_store import Chunk

logger = logging.getLogger(__name__)

_SYSTEM = (
    "Sos un reordenador de relevancia. Recibís una PREGUNTA y una lista de "
    "FRAGMENTOS numerados. Devolvé SOLO los números de los fragmentos más "
    "relevantes para responder la pregunta, del más al menos relevante, "
    "separados por comas. No expliques nada: solo los números."
)


def _build_user(question: str, candidates: list[Chunk], limit: int = 500) -> str:
    lines = [f"PREGUNTA: {question}", "", "FRAGMENTOS:"]
    for i, c in enumerate(candidates, start=1):
        lines.append(f"[{i}] {c.text[:limit]}")
    return "\n".join(lines)


def _parse_order(text: str, n: int) -> list[int]:
    """Extrae los índices válidos (1..n), sin duplicados, en orden de aparición."""
    seen: set[int] = set()
    order: list[int] = []
    for match in re.findall(r"\d+", text):
        idx = int(match)
        if 1 <= idx <= n and idx not in seen:
            seen.add(idx)
            order.append(idx)
    return order


def rerank(
    ollama: OllamaClient, question: str, candidates: list[Chunk], top_k: int
) -> list[Chunk]:
    """Reordena `candidates` por relevancia y devuelve los mejores `top_k`."""
    if len(candidates) <= top_k:
        return candidates[:top_k]

    try:
        raw = ollama.chat(
            _SYSTEM, _build_user(question, candidates),
            temperature=0.0, num_predict=64,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("rerank falló, uso el orden vectorial: %s", exc)
        return candidates[:top_k]

    order = _parse_order(raw, len(candidates))
    if not order:
        return candidates[:top_k]

    reranked = [candidates[i - 1] for i in order]
    # Completar con los que el LLM no mencionó (por si devuelve menos de top_k).
    mentioned = set(order)
    reranked += [c for i, c in enumerate(candidates, start=1) if i not in mentioned]
    return reranked[:top_k]
