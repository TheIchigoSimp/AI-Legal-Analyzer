"""Pydantic models for query and analysis responses."""

from typing import Literal, Optional
from pydantic import BaseModel, Field

class ClassificationResult(BaseModel):
    """LLM output for clause classification."""
    clause_type: str = Field(description="e.g. Termination, Liability, Payment, Confidentiality, Indemnity, IP, Warranty, etc.")
    importance: Literal["Low", "Medium", "High"] = Field(description="How important this clause is")

class RiskResult(BaseModel):
    """LLM output for risk assessment."""
    risk_level: Literal["Low", "Medium", "High"] = Field(description="Risk level of the clause")
    risk_reason: str = Field(description="Brief explanation of why this risk level was assigned")

class QueryRequest(BaseModel):
    """Request body for RAG question answering."""
    question: str = Field(..., min_length=5)
    top_k: int = Field(default=5, ge=1, le=20)
    doc_id: str | None = Field(default=None, description="Optional document ID to scope the search")

class QueryResponse(BaseModel):
    """Structured response from the RAG chain."""
    answer: str
    referenced_clauses: list[str]
    overall_risk: Literal["Low", "Medium", "High"]
    confidence: float = Field(ge=0.0, le=1.0)