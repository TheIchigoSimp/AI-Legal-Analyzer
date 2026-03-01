"""Pydantic models for clause data"""

from typing import List, Optional, Literal
from pydantic import BaseModel

class Clause(BaseModel):
    """A single extracted clause from a pdf."""
    clause_id: str
    section_title: str
    text: str
    page: int

class ClassifiedClause(Clause):
    """A clause with classification and risk metadata."""
    clause_type: Optional[str] = None
    importance: Optional[Literal["Low", "Medium", "High"]] = None
    risk_level: Optional[Literal["Low", "Medium", "High"]] = None
    risk_reason: Optional[str] = None

class DocumentOut(BaseModel):
    """Respomse body for an uploaded document."""
    doc_id: str
    filename: str
    page_count: int
    clauses: List[Clause]