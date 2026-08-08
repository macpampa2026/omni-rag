"""Dobles de prueba (fakes) compartidos por los tests.

`FakeOllama` genera embeddings determinísticos por hashing: sin red, rápido y
reproducible dentro de un mismo proceso (que es todo lo que necesitan los tests).
"""
from __future__ import annotations


class FakeOllama:
    embed_model = "fake-embed"
    gen_model = "fake-gen"
    _DIM = 32

    def _vec(self, text: str) -> list[float]:
        vec = [0.0] * self._DIM
        for token in text.lower().split():
            vec[hash(token) % self._DIM] += 1.0
        return vec if any(vec) else [1.0] + [0.0] * (self._DIM - 1)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_one(self, text: str) -> list[float]:
        return self._vec(text)

    def chat(self, system, user, temperature: float = 0.1, num_predict: int = 500) -> str:
        return "Respuesta de prueba basada en el contexto [1]."

    def ping(self) -> bool:
        return True

    def close(self) -> None:  # pragma: no cover
        pass
