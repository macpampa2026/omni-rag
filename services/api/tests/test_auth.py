"""Tests de la autenticación por API key."""
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.vector_store import InMemoryVectorStore
from tests.fakes import FakeOllama


def _client_with_key(tmp_path, key):
    app = create_app()
    app.state.settings = Settings(
        index_path=str(tmp_path / "i.json"), api_key=key, database_url=None
    )
    app.state.ollama = FakeOllama()
    app.state.store = InMemoryVectorStore(app.state.settings.index_path)
    return TestClient(app)


def test_ask_requires_api_key_when_configured(tmp_path):
    client = _client_with_key(tmp_path, "secreta")
    assert client.post("/ask", json={"question": "hola"}).status_code == 401
    ok = client.post(
        "/ask", json={"question": "hola"}, headers={"X-API-Key": "secreta"}
    )
    assert ok.status_code == 200


def test_health_never_requires_key(tmp_path):
    client = _client_with_key(tmp_path, "secreta")
    assert client.get("/health").status_code == 200
