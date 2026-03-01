import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.database import init_db

from app.api.auth_routes import router as auth_router
from app.api.document_routes import router as document_router
from app.api.query_routes import router as query_router
from app.api.chat_routes import router as chat_router

from app.services.vector_store import load_index
from app.services.vector_store import add_clauses as add_clauses_to_index

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    setup_logging()
    settings = get_settings()

    # Ensure required directories exist
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.faiss_index_path).mkdir(parents=True, exist_ok=True)
    Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
    logger.info("Starting AI Legal Analyzer")

    # Initialize DB
    init_db()
    # Load FAISS index from disk (if exists)
    load_index()

    logger.info("Upload dir: %s", settings.upload_dir)
    logger.info("FAISS index: %s", settings.faiss_index_path)
    logger.info("Database: %s", settings.database_path)

    # FAISS loading will be added in later phases
    yield
    logger.info("Shutting down AI Legal Analyzer")

def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Legal / Policy Analyzer",
        description="Enterprise-grade legal document analysis with RAG-powered Q&A",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["System"])
    async def health_check():
        return {"status": "healthy",  "service": "legal-analyzer"}

    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    app.include_router(document_router, prefix="/documents", tags=["Documents"])
    app.include_router(query_router, prefix="/query", tags=["Query"])
    app.include_router(chat_router, prefix="/chat", tags=["Chat"])
    
    return app

app = create_app()