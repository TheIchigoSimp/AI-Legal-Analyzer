"""FAISS vector store manager with disk persistence."""

import logging
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from app.services.embedding import get_embeddings_model
from app.core.config import get_settings

logger = logging.getLogger(__name__)

_vector_store: FAISS | None = None


def get_vector_store() -> FAISS | None:
    """Return the current in-memory FAISS store (may be None if empty)."""
    return _vector_store


def load_index() -> None:
    """Load FAISS index from disk if it exists."""
    global _vector_store
    settings = get_settings()
    index_path = Path(settings.faiss_index_path)

    if (index_path / "index.faiss").exists():
        logger.info("Loading FAISS index from %s", index_path)
        _vector_store = FAISS.load_local(
            str(index_path),
            get_embeddings_model(),
            allow_dangerous_deserialization=True,
        )
        logger.info("FAISS index loaded with %d vectors", _vector_store.index.ntotal)
    else:
        logger.info("No existing FAISS index found, starting fresh")
        _vector_store = None


def persist_index() -> None:
    """Save the current FAISS index to disk."""
    global _vector_store
    if _vector_store is None:
        logger.warning("No FAISS index to persist")
        return

    settings = get_settings()
    index_path = Path(settings.faiss_index_path)
    index_path.mkdir(parents=True, exist_ok=True)
    _vector_store.save_local(str(index_path))
    logger.info("FAISS index persisted to %s", index_path)


def add_clauses(clauses: list[dict]) -> None:
    """
    Embed and add classified clauses to the FAISS index.
    Each clause dict should have: clause_id, section_title, text, page, clause_type, risk_level
    """
    global _vector_store

    documents = []
    for c in clauses:
        doc = Document(
            page_content=c["text"],
            metadata={
                "clause_id": c.get("clause_id") or c.get("id", ""),
                "document_id": c.get("document_id", ""),
                "section_title": c.get("section_title", "Untitled"),
                "clause_type": c.get("clause_type", "General"),
                "risk_level": c.get("risk_level", "Medium"),
                "page": c.get("page", 0),
},
        )
        documents.append(doc)

    embeddings_model = get_embeddings_model()

    if _vector_store is None:
        _vector_store = FAISS.from_documents(documents, embeddings_model)
        logger.info("Created new FAISS index with %d documents", len(documents))
    else:
        _vector_store.add_documents(documents)
        logger.info("Added %d documents to FAISS index (total: %d)", len(documents), _vector_store.index.ntotal)

    # Auto-persist after adding
    persist_index()


def search(query: str, k: int = 5) -> list[Document]:
    """Search the FAISS index for the most similar clauses."""
    global _vector_store
    if _vector_store is None:
        logger.warning("FAISS index is empty, cannot search")
        return []

    results = _vector_store.similarity_search(query, k=k)
    logger.info("FAISS search returned %d results for query: %s", len(results), query[:50])
    return results
