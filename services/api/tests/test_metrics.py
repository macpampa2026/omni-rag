def test_metrics_endpoint_exposes_prometheus(client):
    client.get("/health")  # genera al menos un request medido
    r = client.get("/metrics")
    assert r.status_code == 200
    body = r.text
    assert "omnirag_http_requests_total" in body
    assert "omnirag_rag_queries_total" in body
    assert "omnirag_http_request_duration_seconds" in body
