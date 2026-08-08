"""Almacén de vectores.

Definimos la INTERFAZ (`VectorStore`) por separado de la implementación.
Hoy usamos `InMemoryVectorStore` (persistido en un JSON). En el M2 vamos a
agregar `PgVectorStore` (PostgreSQL + pgvector) SIN tocar la lógica de negocio:
ese es el punto de tener la abstracción (inversión de dependencias).
"""
from __future__ import annotations

import json
import math
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass
class Chunk:
    """Un fragmento indexado y su vector."""

    id: int
    doc_id: str
    title: str
    text: str
    vec: list[float]
    page: int | None = None
    score: float = field(default=0.0, compare=False)


def normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=False))


class VectorStore(Protocol):
    """Contrato que cualquier backend de vectores debe cumplir."""

    def add(self, chunks: list[Chunk]) -> None: ...
    def search(self, query_vec: list[float], k: int) -> list[Chunk]: ...
    def list_documents(self) -> list[dict]: ...
    def count_chunks(self) -> int: ...


class InMemoryVectorStore:
    """Búsqueda por similitud coseno en memoria, con persistencia en JSON.

    Los vectores se guardan normalizados, así la similitud coseno se reduce a
    un producto punto. Es thread-safe con un lock simple.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._chunks: list[Chunk] = []
        self._next_id = 0
        self._lock = threading.Lock()
        self._load()

    # --- Persistencia ---
    def _load(self) -> None:
        if not self._path.exists():
            return
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        self._chunks = [Chunk(**c) for c in raw.get("chunks", [])]
        self._next_id = max((c.id for c in self._chunks), default=-1) + 1

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {"chunks": [asdict(c) for c in self._chunks]}
        # asdict incluye 'score'; lo dejamos, es inofensivo para recargar.
        self._path.write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )

    # --- Operaciones ---
    def add(self, chunks: list[Chunk]) -> None:
        with self._lock:
            for c in chunks:
                c.id = self._next_id
                self._next_id += 1
                c.vec = normalize(c.vec)
                self._chunks.append(c)
            self._save()

    def search(self, query_vec: list[float], k: int) -> list[Chunk]:
        q = normalize(query_vec)
        with self._lock:
            scored: list[Chunk] = []
            for c in self._chunks:
                c.score = dot(q, c.vec)
                scored.append(c)
        scored.sort(key=lambda c: c.score, reverse=True)
        return scored[:k]

    def list_documents(self) -> list[dict]:
        with self._lock:
            docs: dict[str, dict] = {}
            for c in self._chunks:
                d = docs.setdefault(
                    c.doc_id, {"doc_id": c.doc_id, "title": c.title, "chunks": 0}
                )
                d["chunks"] += 1
            return list(docs.values())

    def count_chunks(self) -> int:
        with self._lock:
            return len(self._chunks)
