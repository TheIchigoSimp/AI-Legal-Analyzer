"""Document upload and analysis routes."""

import uuid
import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from app.core.config import get_settings
from app.api.deps import get_current_user

from app.db.database import get_db
from app.db.repositories import (
    create_document, insert_clauses, get_clauses_by_document,
    get_document, list_user_documents, is_document_analyzed,
    update_clause_classification, delete_document
)

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
            clauses = get_clauses_by_document(conn, doc["id"])
            doc["clause_count"] = len(clauses)
        return docs
    finally:
        conn.close()


@router.get("/stats")
def get_stats(current_user: dict = Depends(get_current_user)):
    """Get analysis statistics for the current user's documents."""
    conn = get_db()
    try:
        docs = list_user_documents(conn, current_user["username"])
        total_docs = len(docs)
        analyzed_docs = sum(1 for d in docs if is_document_analyzed(conn, d["id"]))

        all_clauses = []
        for doc in docs:
            clauses = get_clauses_by_document(conn, doc["id"])
            for c in clauses:
                c["doc_filename"] = doc["filename"]
            all_clauses.extend(clauses)

        total_clauses = len(all_clauses)
        analyzed_clauses = [c for c in all_clauses if c.get("clause_type")]

        risk_counts = {"High": 0, "Medium": 0, "Low": 0}
        for c in analyzed_clauses:
            level = c.get("risk_level", "Low")
            if level in risk_counts:
                risk_counts[level] += 1

        top_risky = sorted(
            [c for c in analyzed_clauses if c.get("risk_level") == "High"],
            key=lambda c: c.get("section_title", ""),
        )[:5]

        return {
            "total_documents": total_docs,
            "analyzed_documents": analyzed_docs,
            "total_clauses": total_clauses,
            "analyzed_clauses": len(analyzed_clauses),
            "risk_distribution": risk_counts,
            "top_risky_clauses": [
                {
                    "clause_id": c["id"],
                    "section_title": c.get("section_title", "Untitled"),
                    "clause_type": c.get("clause_type"),
                    "risk_reason": c.get("risk_reason"),
                    "doc_filename": c.get("doc_filename"),
                    "page": c.get("page"),
                }
                for c in top_risky
            ],
        }
    finally:
        conn.close()

@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_endpoint(doc_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a document, its clauses, and uploaded PDF."""
    conn = get_db()
    try:
        doc = get_document(conn, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        if doc["uploaded_by"] != current_user["username"]:
            raise HTTPException(status_code=403, detail="Not your document")

        # Delete from DB
        delete_document(conn, doc_id)

        # Delete PDF file
        settings = get_settings()
        pdf_path = Path(settings.upload_dir) / f"{doc_id}.pdf"
        if pdf_path.exists():
            pdf_path.unlink()
            logger.info("Deleted PDF file: %s", pdf_path)

    finally:
        conn.close()

from fastapi.responses import FileResponse

@router.get("/{doc_id}/pdf")
def get_document_pdf(doc_id: str, current_user: dict = Depends(get_current_user)):
    """Serve the uploaded PDF file."""
    conn = get_db()
    try:
        doc = get_document(conn, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
    finally:
        conn.close()

    settings = get_settings()
    pdf_path = Path(settings.upload_dir) / f"{doc_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=doc["filename"],
    )

@router.get("/{doc_id}/export")
def export_document_report(doc_id: str, current_user: dict = Depends(get_current_user)):
    """Export analysis report as JSON."""
    conn = get_db()
    try:
        doc = get_document(conn, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        rows = get_clauses_by_document(conn, doc_id)
        clauses = [
            {
                "section_title": r.get("section_title", "Untitled"),
                "text": r["text"],
                "page": r["page"],
                "clause_type": r.get("clause_type"),
                "importance": r.get("importance"),
                "risk_level": r.get("risk_level"),
                "risk_reason": r.get("risk_reason"),
            }
            for r in rows
        ]

        risk_counts = {"High": 0, "Medium": 0, "Low": 0}
        for c in clauses:
            level = c.get("risk_level")
            if level in risk_counts:
                risk_counts[level] += 1

        report = {
            "document": {
                "filename": doc["filename"],
                "page_count": doc["page_count"],
                "uploaded_by": doc["uploaded_by"],
                "created_at": doc["created_at"],
                "is_analyzed": is_document_analyzed(conn, doc_id),
            },
            "summary": {
                "total_clauses": len(clauses),
                "risk_distribution": risk_counts,
            },
            "clauses": clauses,
        }
        return report
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

@router.get("/{doc_id}/clauses")
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
            {
                "clause_id": r["id"],
                "section_title": r["section_title"] or "Untitled",
                "text": r["text"],
                "page": r["page"],
                "clause_type": r.get("clause_type"),
                "importance": r.get("importance"),
                "risk_level": r.get("risk_level"),
                "risk_reason": r.get("risk_reason"),
            }
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

