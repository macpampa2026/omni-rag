"""initial: extensión pgvector + tablas documents y chunks

Revision ID: 0001
Revises:
Create Date: 2026-08-08
"""
import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

from app.config import get_settings

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

_DIM = get_settings().embed_dim


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "documents",
        sa.Column("doc_id", sa.String(255), primary_key=True),
        sa.Column("title", sa.String(512), nullable=False, server_default=""),
    )
    op.create_table(
        "chunks",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "doc_id",
            sa.String(255),
            sa.ForeignKey("documents.doc_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("page", sa.Integer, nullable=True),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("embedding", Vector(_DIM), nullable=False),
    )
    op.create_index("ix_chunks_doc_id", "chunks", ["doc_id"])
    # Índice ANN (HNSW) para búsqueda por distancia coseno.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_chunks_embedding_hnsw "
        "ON chunks USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_chunks_embedding_hnsw")
    op.drop_index("ix_chunks_doc_id", table_name="chunks")
    op.drop_table("chunks")
    op.drop_table("documents")
