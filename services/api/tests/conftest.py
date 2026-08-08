"""Fixtures de test.

Usamos un vector store en un archivo temporal y un cliente Ollama de mentira
(fake), así los tests corren rápido y sin depender del motor real ni de una
base de datos.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.vector_store import InMemoryVectorStore
from tests.fakes import FakeOllama


@pytest.fixture
def client(tmp_path):
    app = create_app()
    app.state.settings = Settings(
        index_path=str(tmp_path / "index.json"), api_key=None, database_url=None
    )
    app.state.ollama = FakeOllama()
    app.state.store = InMemoryVectorStore(app.state.settings.index_path)
    with TestClient(app) as c:
        yield c
