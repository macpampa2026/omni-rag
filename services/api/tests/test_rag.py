from app.services import rag
from app.services.vector_store import Chunk, InMemoryVectorStore
from tests.fakes import FakeOllama


def test_answer_returns_fallback_when_no_documents(tmp_path):
    store = InMemoryVectorStore(tmp_path / "i.json")
    r = rag.answer(
        store, FakeOllama(), question="cualquier cosa?", k=5,
        temperature=0.1, num_predict=50, gen_model="fake",
    )
    assert r.answer == rag.FALLBACK
    assert r.sources == []


def test_answer_includes_cited_source(tmp_path):
    store = InMemoryVectorStore(tmp_path / "i.json")
    ollama = FakeOllama()
    text = "El plazo de devolucion es de 30 dias corridos"
    store.add([Chunk(id=-1, doc_id="d1", title="Politica", text=text,
                     vec=ollama.embed_one(text), page=3)])
    r = rag.answer(
        store, ollama, question="plazo de devolucion", k=3,
        temperature=0.1, num_predict=50, gen_model="fake",
    )
    assert len(r.sources) == 1
    assert r.sources[0].doc_id == "d1"
    assert r.sources[0].page == 3
    assert r.sources[0].n == 1
