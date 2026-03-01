"""Query routes — RAG-based question answering."""

import logging
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.query import QueryRequest, QueryResponse
from app.services.qa_chain import ask_question

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=QueryResponse)
def query(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user),
):
    """Ask a question about uploaded legal documents using RAG."""
    logger.info("User '%s' asked: %s", current_user["username"], request.question)

    response = ask_question(
        question=request.question,
        top_k=request.top_k,
        doc_id=request.doc_id,
    )

    logger.info("Answered with confidence: %.2f", response.confidence)
    return response
