"""Cliente HTTP para Ollama (embeddings + generación de texto).

Aísla toda la comunicación con el motor local en un solo lugar, para que el
resto de la app no sepa que por debajo hay Ollama. Es síncrono a propósito:
FastAPI ejecuta los handlers `def` en un threadpool, así no bloqueamos el loop.
"""
from __future__ import annotations

import httpx


class OllamaError(RuntimeError):
    """Error al comunicarse con el motor local de Ollama."""


class OllamaClient:
    def __init__(
        self,
        base_url: str,
        embed_model: str,
        gen_model: str,
        timeout: float = 300.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.embed_model = embed_model
        self.gen_model = gen_model
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    # --- Embeddings ---
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Vectoriza una lista de textos. Intenta el endpoint por lotes y,
        si no está disponible, cae a uno por uno."""
        if not texts:
            return []
        try:
            resp = self._client.post(
                "/api/embed", json={"model": self.embed_model, "input": texts}
            )
            resp.raise_for_status()
            embs = resp.json().get("embeddings")
            if embs and len(embs) == len(texts):
                return embs
        except httpx.HTTPError:
            pass  # caemos al modo uno-por-uno

        out: list[list[float]] = []
        for text in texts:
            try:
                resp = self._client.post(
                    "/api/embeddings",
                    json={"model": self.embed_model, "prompt": text},
                )
                resp.raise_for_status()
                out.append(resp.json()["embedding"])
            except httpx.HTTPError as exc:  # pragma: no cover - error de red
                raise OllamaError(f"Fallo al generar embeddings: {exc}") from exc
        return out

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]

    # --- Generación ---
    def chat(
        self,
        system: str,
        user: str,
        temperature: float = 0.1,
        num_predict: int = 500,
    ) -> str:
        payload = {
            "model": self.gen_model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
                "top_p": 0.9,
            },
        }
        try:
            resp = self._client.post("/api/chat", json=payload)
            resp.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - error de red
            raise OllamaError(f"Fallo al generar la respuesta: {exc}") from exc
        return resp.json().get("message", {}).get("content", "").strip()

    # --- Salud ---
    def ping(self) -> bool:
        try:
            resp = self._client.get("/api/tags")
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    def close(self) -> None:
        self._client.close()
