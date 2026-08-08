"""Schemas Pydantic: contrato público de la API (entrada y salida)."""
from pydantic import BaseModel, Field


# --- Ingesta ---
class IngestTextRequest(BaseModel):
    doc_id: str = Field(
        ..., description="Identificador único del documento", examples=["politica-devoluciones"]
    )
    title: str = Field("", description="Título legible", examples=["Política de devoluciones"])
    text: str = Field(..., min_length=1, description="Texto plano a indexar")


class IngestResponse(BaseModel):
    doc_id: str
    title: str
    chunks: int = Field(..., description="Cantidad de fragmentos indexados")


class DocumentInfo(BaseModel):
    doc_id: str
    title: str
    chunks: int


# --- Consulta (RAG) ---
class AskRequest(BaseModel):
    question: str = Field(
        ..., min_length=1, examples=["¿Cuántos días tengo para devolver un producto?"]
    )
    top_k: int | None = Field(
        None, ge=1, le=50, description="Cuántos fragmentos recuperar (por defecto, el del server)"
    )


class Source(BaseModel):
    n: int = Field(..., description="Número de cita usado en la respuesta ([n])")
    doc_id: str
    title: str
    page: int | None = None
    score: float = Field(..., description="Similitud coseno con la pregunta (0-1)")
    excerpt: str


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[Source]
    model: str


# --- Salud ---
class HealthResponse(BaseModel):
    status: str = "ok"
    app: str
    version: str


class ReadyResponse(BaseModel):
    status: str
    ollama: str
    indexed_documents: int
    indexed_chunks: int
