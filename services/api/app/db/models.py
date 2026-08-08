"""Modelos ORM: documentos y sus fragmentos vectorizados.

Modelo relacional simple con una relación 1-N (un documento tiene muchos
fragmentos) y una columna vectorial `pgvector` para la búsqueda semántica.
"""
from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import get_settings
from app.db.base import Base

_DIM = get_settings().embed_dim


class DocumentRow(Base):
    __tablename__ = "documents"

    doc_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    title: Mapped[str] = mapped_column(String(512), default="")

    chunks: Mapped[list[ChunkRow]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class ChunkRow(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_id: Mapped[str] = mapped_column(
        ForeignKey("documents.doc_id", ondelete="CASCADE")
    )
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(_DIM))

    document: Mapped[DocumentRow] = relationship(back_populates="chunks")
