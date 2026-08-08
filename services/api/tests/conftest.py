"""Fixtures de test.

Usamos un vector store en un archivo temporal y un cliente Ollama de mentira
(fake), así los tests corren rápido y sin depender del motor real. En el M3
ampliamos con tests de integración.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.vector_store import InMemoryVectorStore


class FakeOllama:
    """Embeddings determinísticos por hashing: sin red, reproducibles."""

    embed_model = "fake-embed"
    gen_model = "fake-gen"
    _DIM = 32

    def _vec(self, text: str) -> list[float]:
        vec = [0.0] * self._DIM
        for token in text.lower().split():
            vec[hash(token) % self._DIM] += 1.0
        return vec or [1.0] + [0.0] * (self._DIM - 1)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_one(self, text: str) -> list[float]:
        return self._vec(text)

    def chat(self, system, user, temperature=0.1, num_predict=500) -> str:
        return "Respuesta de prueba basada en el contexto [1]."

    def ping(self) -> bool:
        return True

    def close(self) -> None:  # pragma: no cover
        pass


@pytest.fixture
def client(tmp_path):
    app = create_app()
    app.state.settings = Settings(index_path=str(tmp_path / "index.json"), api_key=None)
    app.state.ollama = FakeOllama()
    app.state.store = InMemoryVectorStore(app.state.settings.index_path)
    with TestClient(app) as c:
        yield c
