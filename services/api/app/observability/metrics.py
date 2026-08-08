"""Métricas Prometheus del servicio.

Se exponen en `/metrics` en el formato de texto de Prometheus. Un middleware
registra automáticamente los requests HTTP (conteo y latencia); las métricas de
negocio (consultas RAG, documentos ingestados, aciertos de cache) se incrementan
en el punto correspondiente del código.
"""
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQUESTS = Counter(
    "omnirag_http_requests_total",
    "Total de requests HTTP",
    ["method", "path", "status"],
)
LATENCY = Histogram(
    "omnirag_http_request_duration_seconds",
    "Latencia de los requests HTTP en segundos",
    ["method", "path"],
)

RAG_QUERIES = Counter(
    "omnirag_rag_queries_total", "Cantidad de consultas RAG (/ask)"
)
DOCS_INGESTED = Counter(
    "omnirag_documents_ingested_total", "Cantidad de documentos ingestados"
)
EMBED_CACHE = Counter(
    "omnirag_embedding_cache_total",
    "Accesos al cache de embeddings",
    ["result"],  # hit | miss
)

__all__ = [
    "CONTENT_TYPE_LATEST",
    "DOCS_INGESTED",
    "EMBED_CACHE",
    "LATENCY",
    "RAG_QUERIES",
    "REQUESTS",
    "generate_latest",
]
