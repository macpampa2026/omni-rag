"""Backend de vectores sobre PostgreSQL + pgvector.

Implementa la MISMA interfaz `VectorStore` que el `InMemoryVectorStore` del M1,
así que el resto de la app (ingesta, recuperación, RAG) no cambia nada: solo se
elige este backend cuando hay `DATABASE_URL` configurada.

La búsqueda usa el operador de distancia coseno de pgvector (`<=>`), que es
invariante a la escala del vector, ordenando por cercanía y devolviendo el
top-K. El `score` reportado es la similitud coseno (1 - distancia).
"""
from __future__ import annotations

import logging

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.db.models import ChunkRow, DocumentRow
from app.services.vector_store import Chunk

logger = logging.getLogger(__name__)


class PgVectorStore:
    def __init__(self, url: str) -> None:
        self._engine = create_engine(url, pool_pre_ping=True, future=True)
        self._Session = sessionmaker(self._engine, expire_on_commit=False, future=True)

    def add(self, chunks: list[Chunk]) -> None:
        with self._Session.begin() as s:
            seen: set[str] = set()
            for c in chunks:
                if c.doc_id not in seen and s.get(DocumentRow, c.doc_id) is None:
                    s.add(DocumentRow(doc_id=c.doc_id, title=c.title or c.doc_id))
                seen.add(c.doc_id)
                s.add(
                    ChunkRow(
                        doc_id=c.doc_id, page=c.page, text=c.text, embedding=c.vec
                    )
                )

    def search(self, query_vec: list[float], k: int) -> list[Chunk]:
        distance = ChunkRow.embedding.cosine_distance(query_vec).label("dist")
        stmt = (
            select(ChunkRow, DocumentRow.title, distance)
            .join(DocumentRow, ChunkRow.doc_id == DocumentRow.doc_id)
            .order_by(distance)
            .limit(k)
        )
        results: list[Chunk] = []
        with self._Session() as s:
            for row, title, dist in s.execute(stmt).all():
                results.append(
                    Chunk(
                        id=row.id,
                        doc_id=row.doc_id,
                        title=title,
                        text=row.text,
                        vec=[],
                        page=row.page,
                        score=1.0 - float(dist),
                    )
                )
        return results

    def list_documents(self) -> list[dict]:
        stmt = (
            select(DocumentRow.doc_id, DocumentRow.title, func.count(ChunkRow.id))
            .join(ChunkRow, ChunkRow.doc_id == DocumentRow.doc_id)
            .group_by(DocumentRow.doc_id, DocumentRow.title)
            .order_by(DocumentRow.doc_id)
        )
        with self._Session() as s:
            return [
                {"doc_id": d, "title": t, "chunks": n}
                for d, t, n in s.execute(stmt).all()
            ]

    def count_chunks(self) -> int:
        with self._Session() as s:
            return int(s.execute(select(func.count(ChunkRow.id))).scalar_one())

    def ping(self) -> bool:
        try:
            with self._engine.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
            return True
        except Exception:  # noqa: BLE001
            return False
