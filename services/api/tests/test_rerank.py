from app.services.rerank import _parse_order, rerank
from app.services.vector_store import Chunk


def _c(i: int) -> Chunk:
    return Chunk(id=i, doc_id="d", title="t", text=f"frag {i}", vec=[], page=None)


def test_parse_order_filters_and_dedupes():
    assert _parse_order("3, 1, 1, 99, 2", 5) == [3, 1, 2]


def test_parse_order_empty_on_garbage():
    assert _parse_order("no hay numeros aca", 5) == []


class _FakeOllama:
    def __init__(self, reply: str) -> None:
        self._reply = reply

    def chat(self, system, user, temperature=0.1, num_predict=500) -> str:
        return self._reply


def test_rerank_reorders_by_llm_output():
    cands = [_c(1), _c(2), _c(3), _c(4)]
    out = rerank(_FakeOllama("3, 1"), "q", cands, top_k=2)
    assert [c.id for c in out] == [3, 1]


def test_rerank_falls_back_to_vector_order_on_bad_output():
    cands = [_c(1), _c(2), _c(3), _c(4)]
    out = rerank(_FakeOllama("sin numeros"), "q", cands, top_k=2)
    assert [c.id for c in out] == [1, 2]


def test_rerank_is_noop_when_candidates_leq_topk():
    cands = [_c(1), _c(2)]
    out = rerank(None, "q", cands, top_k=5)  # ni siquiera llama al LLM
    assert [c.id for c in out] == [1, 2]
