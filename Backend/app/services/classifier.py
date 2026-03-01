"""Clause classification service using Groq LLM."""

import json
import logging
from langchain_groq import ChatGroq
from app.core.config import get_settings
from app.models.query import ClassificationResult

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT = """You are a legal document analyst. Classify the following legal clause.
Return a JSON object with exactly these fields:
- "clause_type": one of [Termination, Liability, Payment, Confidentiality, Indemnity, IP, Warranty, Insurance, Dispute Resolution, Force Majeure, Non-Compete, Data Protection, Governing Law, Amendment, General]
- "importance": one of ["Low", "Medium", "High"]
Clause text:
\"\"\"
{clause_text}
\"\"\"
Return ONLY valid JSON, no other text."""

def _get_llm() -> ChatGroq:
    """Create a Groq LLM instance."""
    settings = get_settings()
    return ChatGroq(
        api_key=settings.groq_api_key,
        model_name=settings.llm_model,
        temperature=0,
        max_tokens=200,
    )

def classify_clause(clause_text: str) -> ClassificationResult:
    """Classify a single clause using the LLM."""
    llm = _get_llm()
    prompt = CLASSIFICATION_PROMPT.format(clause_text=clause_text[:2000])
    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        # Parse JSON from response (handle markdown code blocks)
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        data = json.loads(content)
        return ClassificationResult(**data)
    except Exception as e:
        logger.warning("Classification failed for clause: %s", str(e))
        return ClassificationResult(clause_type="General", importance="Medium")

def classify_clauses(clauses: list[dict]) -> list[ClassificationResult]:
    """Classify a batch of clauses. Processes sequentially to respect rate limits."""
    results = []
    for i, clause in enumerate(clauses):
        logger.info("Classifying clause %d/%d: %s", i + 1, len(clauses), clause.get("clause_id", ""))
        result = classify_clause(clause["text"])
        results.append(result)
    return results