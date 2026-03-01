"""RAG question-answering chain using FAISS retrieval + Groq LLM."""

import json
import logging
from typing import Optional

from langchain_groq import ChatGroq
from app.core.config import get_settings
from app.services.vector_store import search as faiss_search
from app.models.query import QueryResponse
logger = logging.getLogger(__name__)

QA_PROMPT = """You are a legal analyst. Answer the user's question based ONLY on the provided legal clauses below.

Rules:
- Only use information from the provided clauses — do NOT make up information
- Cite specific clause IDs in your answer
- If the clauses don't contain enough information, say so clearly
- Assess the overall risk based on the clauses found
- Use the conversation history to understand follow-up questions

Provided clauses:
{context}

{history_section}

User question: {question}

Return a JSON object with exactly these fields:
- "answer": your detailed answer (cite only the section title part and not the complete id)
- "referenced_clauses": list of clause IDs you referenced
- "overall_risk": one of ["Low", "Medium", "High"] based on the relevant clauses
- "confidence": a float between 0.0 and 1.0 indicating how confident you are

Return ONLY valid JSON, no other text.
"""

def get_llm() -> ChatGroq: 
    settings = get_settings()
    return ChatGroq(
        api_key=settings.groq_api_key,
        model_name=settings.llm_model,
        temperature=0,
        max_tokens=1000
    )

def _format_context(documents: list) -> str:
    """Format retrieved FAISS documents into a context string for the LLM."""
    parts = []
    for doc in documents:
        meta = doc.metadata
        parts.append(
            f"[Clause_ID: {meta.get('clause_id', 'unknown')}]\n"
            f"Type: {meta.get('clause_type', 'Unknown')} |"
            f"Risk: {meta.get('risk_level', 'Unknown')} |"
            f"Page: {meta.get('page', '?')}\n"
            f"Text: {doc.page_content}\n"
        )
    return "\n---\n".join(parts)

def ask_question(
    question: str,
    top_k: int = 5,
    doc_id: Optional[str] = None,
    conversation_history: list = None,
) -> QueryResponse:
    """Answer a question using RAG with conversation memory.
    If doc_id is provided, only search within that document."""

    # Step 1: Retrieve from FAISS
    # Fetch extra results if filtering by doc_id
    fetch_k = top_k * 3 if doc_id else top_k
    results = faiss_search(question, k=fetch_k)

    # Step 2: Filter by document if specified
    if doc_id:
        results = [r for r in results if r.metadata.get("document_id") == doc_id][:top_k]
    if not results:
        return QueryResponse(
            answer="No relevant clauses found for your question. Please upload and analyze a document first.",
            referenced_clauses=[],
            overall_risk="Low",
            confidence=0.0,
        )

    # Step 3: Build context and query LLM
    context = _format_context(results)
    llm = get_llm()

    # Format conversation history
    history_section = ""
    if conversation_history:
        history_lines = []
        for msg in conversation_history[-10:]:  # Last 10 messages max
            role = "User" if msg["role"] == "user" else "Assistant"
            history_lines.append(f"{role}: {msg['content']}")
        history_section = "Conversation history:\n" + "\n".join(history_lines)

    prompt = QA_PROMPT.format(context=context, question=question, history_section=history_section)

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()

        # Parse JSON (handle markdown code blocks)
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
                content = content.strip()

        data = json.loads(content)
        return QueryResponse(**data)
    except Exception as e:
        logger.error("QA chain failed: %s", str(e))

        # Return a graceful fallback
        clause_ids = [r.metadata.get("clause_id", "") for r in results]
        return QueryResponse(
            answer=f"I found {len(results)} relevant clauses but encountered an error generating the answer.",
            referenced_clauses=clause_ids,
            overall_risk="Medium",
            confidence=0.2,
        )