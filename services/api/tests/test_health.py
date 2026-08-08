def test_health_liveness(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["app"] == "omni-rag"


def test_readiness_reports_index(client):
    r = client.get("/health/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["ollama"] == "up"
    assert body["indexed_chunks"] == 0


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["name"] == "omni-rag"
