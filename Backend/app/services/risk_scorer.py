"""Risk scoring service — hybrid heuristic + LLM approach."""

import json
import logging
from langchain_groq import ChatGroq
from app.core.config import get_settings
from app.models.query import RiskResult

logger = logging.getLogger(__name__)

# Keywords that indicate elevated risk
HIGH_RISK_KEYWORDS = [
    "indemnify", "indemnification", "unlimited liability",
    "sole discretion", "waive", "waiver", "penalty", "penalties",
    "liquidated damages", "consequential damages", "termination for convenience",
    "non-compete", "non-solicitation", "exclusive", "irrevocable",
]

MEDIUM_RISK_KEYWORDS = [
    "liability", "limitation", "damages", "breach", "default",
    "terminate", "confidential", "obligation", "warranty", "guarantee",
]

RISK_PROMPT = """You are a legal risk analyst. Assess the risk level of the following legal clause.

Consider:
- Does it create significant obligations or liabilities?
- Are there unfavorable terms for one party?
- Could it lead to financial exposure or legal disputes?

Return a JSON object with exactly these fields:
- "risk_level": one of ["Low", "Medium", "High"]
- "risk_reason": a brief 1-2 sentence explanation

Clause text:
\"\"\"
{clause_text}
\"\"\"

Return ONLY valid JSON, no other text."""


def _get_llm() -> ChatGroq:
    settings = get_settings()
    return ChatGroq(
        api_key=settings.groq_api_key,
        model_name=settings.llm_model,
        temperature=0,
        max_tokens=200,
    )


def _heuristic_risk(text: str) -> str | None:
    """
    Keyword-based risk check. Returns 'High', 'Medium', or None.
    None means defer to LLM.
    """
    text_lower = text.lower()
    for keyword in HIGH_RISK_KEYWORDS:
        if keyword in text_lower:
            return "High"
    for keyword in MEDIUM_RISK_KEYWORDS:
        if keyword in text_lower:
            return "Medium"
    return None


def score_risk(clause_text: str) -> RiskResult:
    """Score risk for a single clause using heuristics + LLM."""

    # Step 1: Heuristic check
    heuristic = _heuristic_risk(clause_text)

    # Step 2: LLM reasoning
    llm = _get_llm()
    prompt = RISK_PROMPT.format(clause_text=clause_text[:2000])

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()

        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        data = json.loads(content)
        llm_result = RiskResult(**data)

        # Step 3: Combine — heuristic High always wins
        if heuristic == "High":
            return RiskResult(
                risk_level="High",
                risk_reason=f"[Keyword flagged] {llm_result.risk_reason}",
            )

        return llm_result

    except Exception as e:
        logger.warning("Risk scoring failed: %s", str(e))
        return RiskResult(
            risk_level=heuristic or "Medium",
            risk_reason="Risk assessment unavailable — defaulted based on heuristics",
        )


def score_clauses(clauses: list[dict]) -> list[RiskResult]:
    """Score risk for a batch of clauses. Sequential to respect rate limits."""
    results = []
    for i, clause in enumerate(clauses):
        logger.info("Scoring risk %d/%d: %s", i + 1, len(clauses), clause.get("clause_id", ""))
        result = score_risk(clause["text"])
        results.append(result)
    return results
