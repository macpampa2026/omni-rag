"""Limpieza y troceado (chunking) de texto para indexar."""
from __future__ import annotations

import re


def clean(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def chunk_text(
    text: str, chunk_chars: int = 1000, overlap: int = 150
) -> list[str]:
    """Parte el texto en fragmentos solapados.

    El solape evita cortar una idea justo en el límite de un fragmento, lo que
    mejora la recuperación de contexto relevante.
    """
    text = clean(text)
    if len(text) < 40:
        return []
    step = max(chunk_chars - overlap, 1)
    pieces: list[str] = []
    i = 0
    while i < len(text):
        piece = text[i : i + chunk_chars].strip()
        if len(piece) > 60:
            pieces.append(piece)
        i += step
    return pieces
