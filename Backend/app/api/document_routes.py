"""Document upload and analysis routes."""

import uuid
import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from app.core.config import get_settings
from app.api.deps import get_current_user

from app.db.database import get_db
from app.db.repositories import create_document, insert_clauses, get_clauses_by_document, get_document, list_user_documents, is_document_analyzed

from app.services.pdf_extractor import extract_pages
from app.services.segmenter import segment_document
from app.models.clause import Clause, DocumentOut

from app.services.classifier import classify_clauses
from app.services.risk_scorer import score_clauses
from app.db.repositories import update_clause_classification
from app.models.clause import ClassifiedClause

from app.services.vector_store import add_clauses as add_clauses_to_index


logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=list[dict])
def list_documents(current_user: dict = Depends(get_current_user)):
    """List all documents for the current user."""
    conn = get_db()
    try:
        docs = list_user_documents(conn, current_user["username"])
        for doc in docs:
            doc["is_analyzed"] = is_document_analyzed(conn, doc["id"])
        return docs
    finally:
        conn.close()


@router.get("/{doc_id}")
def get_document_detail(doc_id: str, current_user: dict = Depends(get_current_user)):
    """Get a single document with analysis status."""
    conn = get_db()
    try:
        doc = get_document(conn, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        doc = dict(doc)
        doc["is_analyzed"] = is_document_analyzed(conn, doc_id)
        return doc
    finally:
        conn.close()


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Upload a PDF, extract text, and segment into clauses."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted",
        )
    settings = get_settings()
    doc_id = str(uuid.uuid4())
    # Save uploaded file
    upload_path = Path(settings.upload_dir) / f"{doc_id}.pdf"
    try:
        content = file.file.read()
        upload_path.write_bytes(content)
        logger.info("Saved PDF: %s -> %s", file.filename, upload_path)
    except Exception as e:
        logger.error("Failed to save file: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")
    # Extract text
    pages = extract_pages(upload_path)
    if not pages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract any text from PDF",
        )
    # Segment into clauses
    clauses = segment_document(pages, doc_id)
    # Store in database
    conn = get_db()
    try:
        create_document(conn, doc_id, file.filename, current_user["username"], len(pages))
        insert_clauses(conn, doc_id, [c.model_dump() for c in clauses])
    finally:
        conn.close()
    return DocumentOut(
        doc_id=doc_id,
        filename=file.filename,
        page_count=len(pages),
        clauses=clauses,
    )

@router.get("/{doc_id}/clauses", response_model=list[Clause])
def get_document_clauses(
    doc_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Retrieve all clauses for a document."""
    conn = get_db()
    try:
        doc = get_document(conn, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        rows = get_clauses_by_document(conn, doc_id)
        return [
            Clause(
                clause_id=r["id"],
                section_title=r["section_title"] or "Untitled",
                text=r["text"],
                page=r["page"],
            )
            for r in rows
        ]
    finally:
        conn.close()

@router.post("/{doc_id}/analyze", response_model=list[ClassifiedClause])
def analyze_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Classify clauses and score risk for an uploaded document."""
    conn = get_db()
    try:
        doc = get_document(conn, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        rows = get_clauses_by_document(conn, doc_id)
        if not rows:
            raise HTTPException(status_code=404, detail="No clauses found for this document")

        clause_dicts = [dict(r) for r in rows]

        # Classify
        classifications = classify_clauses(clause_dicts)

        # Score risk
        risks = score_clauses(clause_dicts)

        # Update DB and build response
        results = []
        for row, cls, risk in zip(clause_dicts, classifications, risks):
            update_clause_classification(
                conn, row["id"], cls.clause_type, cls.importance, risk.risk_level, risk.risk_reason
            )
            results.append(ClassifiedClause(
                clause_id=row["id"],
                section_title=row["section_title"] or "Untitled",
                text=row["text"],
                page=row["page"],
                clause_type=cls.clause_type,
                importance=cls.importance,
                risk_level=risk.risk_level,
                risk_reason=risk.risk_reason,
            ))

        # Store in FAISS
        add_clauses_to_index([{**r.model_dump(), "document_id": doc_id} for r in results])

        logger.info("Analyzed %d clauses for document %s", len(results), doc_id)
        return results
    finally:
        conn.close()
