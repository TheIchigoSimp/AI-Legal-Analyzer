"""Embedding generation service using local HuggingFace model."""

import logging
from langchain_huggingface import HuggingFaceEmbeddings
from app.core.config import get_settings

logger = logging.getLogger(__name__)
_embeddings_model = None

def get_embeddings_model() -> HuggingFaceEmbeddings:
    """Return a cached embeddings model instance."""
    global _embeddings_model
    if _embeddings_model is None:
        settings = get_settings()
        logger.info("Loading embedding model: %s", settings.embedding_model)
        _embeddings_model = HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info("Embedding model loaded successfully")
    return _embeddings_model

def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts."""
    model = get_embeddings_model()
    return model.embed_documents(texts)

def embed_query(text: str) -> list[float]:
    """Generate embedding for a single query."""
    model = get_embeddings_model()
    return model.embed_query(text)