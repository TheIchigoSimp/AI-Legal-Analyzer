"""PDF text extraction service using pdfplumber"""

import logging
from pathlib import Path
import pdfplumber

logger = logging.getLogger(__name__)

def extract_pages(file_path: Path) -> list[dict]:
    """Extract text from each page of a PDF file
        Returns: [{"page": 1, "text": "..."}, ...]
    """

    pages = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages, start = 1):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append({"page": i, "text": text.strip()})
                    logger.info("Extracted %d pages with text from %s", len(pages), file_path.name)
    except Exception as e:
        logger.error("Failed to extract PDF %s: %s", file_path.name, str(e))
        raise
    return pages