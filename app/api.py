
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
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

    try:
        pages = load_pdf_pages(DOCUMENTS_DIR)
        chunks = chunk_pages(pages)

        retriever = EvidenceRetriever()
        retriever.build_index(chunks)

        app.state.pipeline = EvidenceTrustPipeline(retriever)

        logger.info(
            "Evidence index initialized: pages=%d, chunks=%d",
            len(pages),
            len(chunks),
        )
        yield

    except Exception:
        logger.exception("Application initialization failed.")
        raise

    finally:
        app.state.pipeline = None
        logger.info("EvidenceTrust AI shutdown complete.")


app = FastAPI(
    title="EvidenceTrust AI",
    description="Evidence-grounded question answering and verification",
    version="0.1.0",
    lifespan=lifespan,
)


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

        # Do not expose provider internals or credentials in API responses.
        raise HTTPException(
            status_code=502,
            detail=(
                "The answer pipeline could not complete the request. "
                "Check the application log for details."
            ),
        ) from exc
