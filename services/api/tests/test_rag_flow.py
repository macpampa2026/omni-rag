"""Test de flujo completo: ingestar un documento y luego preguntar."""


def test_ingest_then_ask(client):
    # 1) Ingesta
    doc = {
        "doc_id": "devoluciones",
        "title": "Política de devoluciones",
        "text": (
            "El cliente tiene 30 dias corridos para devolver un producto sin uso. "
            "La devolucion se realiza con el ticket de compra. "
            "El reintegro se acredita en el mismo medio de pago original. "
            "Los productos en oferta tambien pueden devolverse dentro del plazo."
        ),
    }
    r = client.post("/documents", json=doc)
    assert r.status_code == 201, r.text
    assert r.json()["chunks"] >= 1

    # 2) El documento aparece listado
    r = client.get("/documents")
    assert r.status_code == 200
    assert any(d["doc_id"] == "devoluciones" for d in r.json())

    # 3) Pregunta -> respuesta con fuentes
    r = client.post("/ask", json={"question": "¿Cuántos días tengo para devolver?"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["answer"]
    assert len(body["sources"]) >= 1
    assert body["sources"][0]["doc_id"] == "devoluciones"


def test_ingest_rejects_short_text(client):
    r = client.post("/documents", json={"doc_id": "x", "title": "", "text": "hola"})
    assert r.status_code == 422
