"""Endpoints de documentos: ingesta de texto/PDF y listado."""
from __future__ import annotations

import io

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.deps import get_ollama, get_settings, get_store, require_api_key
from app.config import Settings
from app.models.schemas import DocumentInfo, IngestResponse, IngestTextRequest
from app.observability import metrics as obs
from app.services import ingest
from app.services.ollama_client import OllamaClient
from app.services.vector_store import VectorStore

router = APIRouter(
    prefix="/documents", tags=["documents"], dependencies=[Depends(require_api_key)]
)


@router.get("", response_model=list[DocumentInfo], summary="Listar documentos")
def list_documents(store: VectorStore = Depends(get_store)) -> list[DocumentInfo]:
    return [DocumentInfo(**d) for d in store.list_documents()]


@router.post(
    "",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingestar texto",
)
def ingest_text_endpoint(
    body: IngestTextRequest,
    store: VectorStore = Depends(get_store),
    ollama: OllamaClient = Depends(get_ollama),
    settings: Settings = Depends(get_settings),
) -> IngestResponse:
    n = ingest.ingest_text(
        store,
        ollama,
        doc_id=body.doc_id,
        title=body.title,
        text=body.text,
        chunk_chars=settings.chunk_chars,
        overlap=settings.chunk_overlap,
    )
    if n == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El texto es demasiado corto para indexar.",
        )
    obs.DOCS_INGESTED.inc()
    return IngestResponse(doc_id=body.doc_id, title=body.title or body.doc_id, chunks=n)


@router.post(
    "/pdf",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingestar PDF (indexa por página)",
)
def ingest_pdf_endpoint(
    doc_id: str = Form(...),
    title: str = Form(""),
    file: UploadFile = File(...),
    store: VectorStore = Depends(get_store),
    ollama: OllamaClient = Depends(get_ollama),
    settings: Settings = Depends(get_settings),
) -> IngestResponse:
    from pypdf import PdfReader  # import perezoso: solo si se usa PDF

    try:
        reader = PdfReader(io.BytesIO(file.file.read()))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"No pude leer el PDF: {exc}",
        ) from exc

    total = 0
    for page_no, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:  # noqa: BLE001
            text = ""
        if text.strip():
            total += ingest.ingest_text(
                store,
                ollama,
                doc_id=doc_id,
                title=title,
                text=text,
                chunk_chars=settings.chunk_chars,
                overlap=settings.chunk_overlap,
                page=page_no,
            )

    if total == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El PDF no tiene texto extraíble para indexar.",
        )
    obs.DOCS_INGESTED.inc()
    return IngestResponse(doc_id=doc_id, title=title or doc_id, chunks=total)
