"""Hybrid clause segmentation: regex-based splitting + fallback chunking."""

import re
import logging
from app.models.clause import Clause
logger = logging.getLogger(__name__)
# Max tokens per clause before fallback chunking kicks in
MAX_CLAUSE_TOKENS = 512

# Regex patterns for detecting legal section headings
SECTION_PATTERNS = [
    r"(?:^|\n)(Section\s+\d+[\.\d]*\.?\s*[^\n]*)",          # Section 1, Section 1.2
    r"(?:^|\n)(Article\s+\d+[\.\d]*\.?\s*[^\n]*)",           # Article 1, Article 1.2
    r"(?:^|\n)(\d+\.\d+[\.\d]*\.?\s+[^\n]+)",               # 1.1, 3.2.1
    r"(?:^|\n)((?:I{1,3}|IV|V|VI{0,3}|IX|X)\.?\s+[^\n]+)",  # Roman numerals
    r"(?:^|\n)([A-Z][A-Z\s]{4,}[A-Z])\s*\n",                # ALL CAPS HEADINGS
]

# Compiled master pattern (OR of all patterns)
MASTER_PATTERN = re.compile("|".join(SECTION_PATTERNS), re.MULTILINE)

def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return len(text) // 4
def _chunk_text(text: str, page: int, base_id: str, doc_id: str, chunk_size: int = 1500, overlap: int = 200) -> list[Clause]:
    """
    Fallback: split long text into overlapping character-based chunks.
    chunk_size and overlap are in characters (~375 and ~50 tokens).
    """
    chunks = []
    start = 0
    idx = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(Clause(
                clause_id=f"{doc_id}-{base_id}-chunk-{idx}",
                section_title="Untitled",
                text=chunk.strip(),
                page=page,
            ))
            idx += 1
        start = end - overlap
    return chunks
def _extract_heading(match: re.Match) -> str:
    """Extract the matched heading text from regex groups."""
    for group in match.groups():
        if group:
            return group.strip()
    return "Untitled"
def segment_document(pages: list[dict], doc_id: str = "") -> list[Clause]:
    """
    Segment extracted PDF pages into clauses using hybrid strategy:
    1. Try regex-based section splitting
    2. Fall back to chunking for unstructured or oversized sections
    """
    full_text = "\n\n".join(
        f"[PAGE:{p['page']}]\n{p['text']}" for p in pages
    )
    # Track which page each character belongs to
    page_map = {}
    offset = 0
    for p in pages:
        marker = f"[PAGE:{p['page']}]\n"
        content = p["text"]
        block = f"{marker}{content}\n\n"
        for i in range(len(block)):
            page_map[offset + i] = p["page"]
        offset += len(block)
    # Try regex splitting
    matches = list(MASTER_PATTERN.finditer(full_text))
    clauses = []
    if matches:
        logger.info("Found %d section headings via regex", len(matches))
        for i, match in enumerate(matches):
            heading = _extract_heading(match)
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
            section_text = full_text[start:end].strip()
            # Remove page markers from text
            clean_text = re.sub(r"\[PAGE:\d+\]\n?", "", section_text).strip()
            page = page_map.get(start, 1)
            # Sanitize heading for use as ID
            safe_heading = re.sub(r"[^\w\d]+", "-", heading.lower()).strip("-")[:30]
            clause_id = f"{doc_id}-section-{i+1}-{safe_heading}" if doc_id else f"section-{i+1}-{safe_heading}"
            if _estimate_tokens(clean_text) > MAX_CLAUSE_TOKENS:
                # Oversized section — chunk it
                logger.info("Section '%s' exceeds token limit, chunking", heading[:30])
                sub_chunks = _chunk_text(clean_text, page, clause_id, doc_id)
                for sc in sub_chunks:
                    sc.section_title = heading
                clauses.extend(sub_chunks)
            else:
                clauses.append(Clause(
                    clause_id=clause_id,
                    section_title=heading,
                    text=clean_text,
                    page=page,
                ))
    else:
        # No structure detected — chunk entire document page by page
        logger.info("No section structure detected, using fallback chunking")
        for p in pages:
            page_clauses = _chunk_text(p["text"], p["page"], f"p{p['page']}", doc_id)
            clauses.extend(page_clauses)
    logger.info("Segmented document into %d clauses", len(clauses))
    return clauses
