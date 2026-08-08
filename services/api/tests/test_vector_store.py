from app.services.vector_store import Chunk, InMemoryVectorStore, normalize


def _chunk(doc_id, text, vec, title="t", page=None):
    return Chunk(id=-1, doc_id=doc_id, title=title, text=text, vec=vec, page=page)


def test_add_and_count(tmp_path):
    store = InMemoryVectorStore(tmp_path / "i.json")
    store.add([_chunk("d1", "a", [1, 0, 0]), _chunk("d1", "b", [0, 1, 0])])
    assert store.count_chunks() == 2
    assert store.list_documents() == [{"doc_id": "d1", "title": "t", "chunks": 2}]


def test_search_orders_by_similarity(tmp_path):
    store = InMemoryVectorStore(tmp_path / "i.json")
    store.add([_chunk("d1", "cerca", [1, 0, 0]), _chunk("d1", "lejos", [0, 1, 0])])
    hits = store.search([1, 0, 0], k=2)
    assert hits[0].text == "cerca"
    assert hits[0].score > hits[1].score


def test_persistence_reloads_from_disk(tmp_path):
    path = tmp_path / "i.json"
    InMemoryVectorStore(path).add([_chunk("d1", "a", [1, 0, 0])])
    reloaded = InMemoryVectorStore(path)  # nueva instancia, mismo archivo
    assert reloaded.count_chunks() == 1


def test_normalize_returns_unit_vector():
    v = normalize([3.0, 4.0])
    assert abs((v[0] ** 2 + v[1] ** 2) - 1.0) < 1e-9
