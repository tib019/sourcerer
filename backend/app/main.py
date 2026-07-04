"""FastAPI-App + Composition Root.

Die gesamte Objekt-Komposition (welcher Provider, welche Parameter) passiert HIER —
der Kern kennt nur Interfaces (ADR-006/007).
"""

from __future__ import annotations

import base64
import logging

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import Settings
from app.errors import (
    EmptyDocumentError,
    FileTooLargeError,
    NotebookNotFoundError,
    UnsupportedFileTypeError,
)
from app.ingest.chunker import Chunker
from app.ingest.extractor import PdfExtractor, PlainTextExtractor
from app.ingest.ingestor import MEDIA_TYPE_PDF, MEDIA_TYPE_TEXT, DocumentIngestor
from app.providers.embeddings import FakeEmbeddings, OpenAIEmbeddings
from app.providers.llm import FakeLLM, OpenAIChat
from app.providers.tts import FakeTTS, OpenAITTS
from app.providers.vector_store import InMemoryVectorStore, PineconeStore
from app.rag.audio_overview import AudioOverviewService
from app.rag.citations import CitationMapper
from app.rag.pipeline import RAGPipeline
from app.rag.prompt_builder import PromptBuilder
from app.rag.retriever import Retriever
from app.repository import InMemoryNotebookRepository, NotebookRepository

logging.basicConfig(level=logging.INFO)


# --- API-Schemas (Pydantic am Rand, Dataclasses im Kern) ---------------------


class CreateNotebookRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class NotebookResponse(BaseModel):
    id: str
    name: str


class PasteTextRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1)


class DocumentResponse(BaseModel):
    id: str
    name: str
    media_type: str
    page_count: int
    chunk_count: int


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class CitationResponse(BaseModel):
    n: int
    document_id: str
    document_name: str
    chunk_index: int
    page: int
    text: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[CitationResponse]


class AudioOverviewResponse(BaseModel):
    summary: str
    media_type: str
    audio_base64: str


# --- Composition Root --------------------------------------------------------


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    settings.validate()

    repository: NotebookRepository
    if settings.providers == "openai":
        from app.repository_supabase import (
            SupabaseNotebookRepository,
            create_supabase_client,
        )

        embedder = OpenAIEmbeddings(api_key=settings.openai_api_key)
        store = PineconeStore(
            api_key=settings.pinecone_api_key, index_name=settings.pinecone_index
        )
        llm = OpenAIChat(api_key=settings.openai_api_key)
        tts = OpenAITTS(api_key=settings.openai_api_key)
        repository = SupabaseNotebookRepository(
            create_supabase_client(settings.supabase_url, settings.supabase_key)
        )
    else:
        embedder = FakeEmbeddings()
        store = InMemoryVectorStore()
        llm = FakeLLM()
        tts = FakeTTS()
        repository = InMemoryNotebookRepository()
    ingestor = DocumentIngestor(
        extractors={MEDIA_TYPE_PDF: PdfExtractor(), MEDIA_TYPE_TEXT: PlainTextExtractor()},
        chunker=Chunker(chunk_size=settings.chunk_size, overlap=settings.chunk_overlap),
        embedder=embedder,
        store=store,
        repository=repository,
        max_bytes=settings.max_upload_bytes,
    )
    audio_overview_service = AudioOverviewService(repository=repository, llm=llm, tts=tts)
    pipeline = RAGPipeline(
        retriever=Retriever(
            embedder=embedder,
            store=store,
            top_k=settings.top_k,
            min_score=settings.min_score,
        ),
        prompt_builder=PromptBuilder(),
        llm=llm,
        citation_mapper=CitationMapper(),
    )

    app = FastAPI(title="Sourcerer", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_error_handlers(app)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "providers": settings.providers}

    @app.post("/notebooks", response_model=NotebookResponse, status_code=201)
    def create_notebook(body: CreateNotebookRequest) -> NotebookResponse:
        notebook = repository.create_notebook(body.name)
        return NotebookResponse(id=notebook.id, name=notebook.name)

    @app.get("/notebooks", response_model=list[NotebookResponse])
    def list_notebooks() -> list[NotebookResponse]:
        return [
            NotebookResponse(id=n.id, name=n.name) for n in repository.list_notebooks()
        ]

    @app.delete("/notebooks/{notebook_id}", status_code=204)
    def delete_notebook(notebook_id: str) -> None:
        repository.delete_notebook(notebook_id)
        # Vektor-Seite miträumen — sonst bleiben Orphans im Namespace (2d).
        store.delete_namespace(notebook_id)

    @app.post(
        "/notebooks/{notebook_id}/documents",
        response_model=DocumentResponse,
        status_code=201,
    )
    async def upload_document(notebook_id: str, file: UploadFile = File(...)) -> DocumentResponse:
        data = await file.read()
        media_type = _normalize_media_type(file.content_type, file.filename or "")
        result = ingestor.ingest(
            data,
            filename=file.filename or "unbenannt",
            media_type=media_type,
            notebook_id=notebook_id,
        )
        return DocumentResponse(
            id=result.document_id,
            name=result.document_name,
            media_type=media_type,
            page_count=result.page_count,
            chunk_count=result.chunk_count,
        )

    @app.post(
        "/notebooks/{notebook_id}/documents/text",
        response_model=DocumentResponse,
        status_code=201,
    )
    def paste_text(notebook_id: str, body: PasteTextRequest) -> DocumentResponse:
        result = ingestor.ingest(
            body.text.encode("utf-8"),
            filename=body.name,
            media_type=MEDIA_TYPE_TEXT,
            notebook_id=notebook_id,
        )
        return DocumentResponse(
            id=result.document_id,
            name=result.document_name,
            media_type=MEDIA_TYPE_TEXT,
            page_count=result.page_count,
            chunk_count=result.chunk_count,
        )

    @app.get(
        "/notebooks/{notebook_id}/documents", response_model=list[DocumentResponse]
    )
    def list_documents(notebook_id: str) -> list[DocumentResponse]:
        return [
            DocumentResponse(
                id=d.id,
                name=d.name,
                media_type=d.media_type,
                page_count=d.page_count,
                chunk_count=d.chunk_count,
            )
            for d in repository.list_documents(notebook_id)
        ]

    @app.post("/notebooks/{notebook_id}/audio-overview", response_model=AudioOverviewResponse)
    def audio_overview(notebook_id: str) -> AudioOverviewResponse:
        repository.get_notebook(notebook_id)
        overview = audio_overview_service.generate(notebook_id)
        return AudioOverviewResponse(
            summary=overview.summary,
            media_type=overview.speech.media_type,
            audio_base64=base64.b64encode(overview.speech.audio).decode("ascii"),
        )

    @app.post("/notebooks/{notebook_id}/chat", response_model=ChatResponse)
    def chat(notebook_id: str, body: ChatRequest) -> ChatResponse:
        repository.get_notebook(notebook_id)
        answer = pipeline.answer(body.question, notebook_id)
        return ChatResponse(
            answer=answer.text,
            citations=[CitationResponse(**c.__dict__) for c in answer.citations],
        )

    return app


def _normalize_media_type(content_type: str | None, filename: str) -> str:
    """Browser liefern für .txt/.md Verschiedenes — Endung ist die verlässlichere Quelle."""
    if content_type == MEDIA_TYPE_PDF or filename.lower().endswith(".pdf"):
        return MEDIA_TYPE_PDF
    if filename.lower().endswith((".txt", ".md")):
        return MEDIA_TYPE_TEXT
    return content_type or "application/octet-stream"


def _register_error_handlers(app: FastAPI) -> None:
    for error_type, status in (
        (UnsupportedFileTypeError, 400),
        (FileTooLargeError, 413),
        (EmptyDocumentError, 422),
        (NotebookNotFoundError, 404),
    ):

        def handler(
            request: Request, exc: Exception, status: int = status
        ) -> JSONResponse:
            return JSONResponse(status_code=status, content={"detail": str(exc)})

        app.add_exception_handler(error_type, handler)


app = create_app()
