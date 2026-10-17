
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.chunker import chunk_pages
from app.config import DOCUMENTS_DIR
from app.document_loader import load_pdf_pages
from app.logging_config import configure_logging, logger
from app.pipeline import EvidenceTrustPipeline
from app.retriever import EvidenceRetriever

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing EvidenceTrust AI.")

    app.state.pipeline = None
    app.state.document_status = {
        "status": "initializing",
        "documents": [],
        "document_count": 0,
        "page_count": 0,
        "chunk_count": 0,
        "error": None,
    }

    try:
        pages = load_pdf_pages(DOCUMENTS_DIR)
        chunks = chunk_pages(pages)

        retriever = EvidenceRetriever()
        retriever.build_index(chunks)

        app.state.pipeline = EvidenceTrustPipeline(retriever)

        # Derive document names from loaded page metadata.
        documents = sorted({
            str(page.get("source", page.get("filename", "unknown")))
            for page in pages
        })

        app.state.document_status = {
            "status": "ready",
            "documents": documents,
            "document_count": len(documents),
            "page_count": len(pages),
            "chunk_count": len(chunks),
            "error": None,
        }

        logger.info(
            "Evidence index initialized: pages=%d, chunks=%d",
            len(pages),
            len(chunks),
        )

    except Exception:
        app.state.document_status.update({
            "status": "error",
            "error": "Document indexing failed. Check application logs.",
        })
        logger.exception("Application initialization failed.")
        raise

    try:
        yield
    finally:
        app.state.pipeline = None
        logger.info("EvidenceTrust AI shutdown complete.")

import logging

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

app = FastAPI(
    title="EvidenceTrust AI",
    description="Evidence-grounded question answering and verification",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "name": "EvidenceTrust AI",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)



@app.get("/health")
def health():
    pipeline = getattr(app.state, "pipeline", None)

    return {
        "status": "ok" if pipeline is not None else "starting",
        "index_ready": pipeline is not None,
    }


@app.get("/documents/status")
def documents_status():
    return getattr(
        app.state,
        "document_status",
        {
            "status": "starting",
            "documents": [],
            "document_count": 0,
            "page_count": 0,
            "chunk_count": 0,
            "error": None,
        },
    )


@app.get("/evaluation/status")
def evaluation_status():
    # This endpoint reports availability only.
    # It does not claim that an evaluation has been run.
    return {
        "status": "available",
        "evaluation_completed": False,
        "labelled_examples": 0,
        "metrics": None,
        "message": (
            "No evaluation results are reported by this status endpoint."
        ),
    }


@app.post("/ask")
def ask(request: AskRequest):
    pipeline = getattr(app.state, "pipeline", None)

    if pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="The evidence index is not ready.",
        )

    try:
        return pipeline.answer(
            question=request.question,
            top_k=request.top_k,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception("Pipeline request failed.")

        raise HTTPException(
            status_code=502,
            detail=(
                "The answer pipeline could not complete the request. "
                "Check the application log for details."
            ),
        ) from exc
