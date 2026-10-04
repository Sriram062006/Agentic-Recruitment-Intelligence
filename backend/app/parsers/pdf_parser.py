"""
PDF Document Parser using PyMuPDF (fitz).
Provides layout-aware block extraction and robust error handling.
"""

import hashlib
import io
from typing import Dict
import fitz  # PyMuPDF

from app.core.logging import get_logger
from app.parsers.base import BaseDocumentParser, ParsedDocument

logger = get_logger("pdf_parser")


class PDFParser(BaseDocumentParser):
    def parse(self, content: bytes, file_name: str) -> ParsedDocument:
        if not content or len(content.strip()) == 0:
            raise ValueError(f"Empty PDF file: '{file_name}' contains 0 bytes")

        file_hash = hashlib.sha256(content).hexdigest()

        try:
            doc = fitz.open(stream=content, filetype="pdf")
        except Exception as e:
            raise ValueError(f"Malformed or unreadable PDF file '{file_name}': {e}") from e

        if doc.is_encrypted:
            raise PermissionError(f"PDF file '{file_name}' is password-encrypted")

        page_count = len(doc)
        text_blocks = []
        metadata: Dict[str, str] = {
            "title": doc.metadata.get("title") or "",
            "author": doc.metadata.get("author") or "",
        }

        for page_idx in range(page_count):
            page = doc[page_idx]
            # Extract blocks: (x0, y0, x1, y1, text, block_no, block_type)
            # block_type == 0 indicates text
            blocks = page.get_text("blocks")
            # Sort top-to-bottom, left-to-right
            sorted_blocks = sorted(blocks, key=lambda b: (b[1], b[0]))
            for b in sorted_blocks:
                if b[6] == 0:  # text block
                    text = b[4].strip()
                    if text:
                        text_blocks.append(text)

        raw_text = "\n\n".join(text_blocks).strip()

        if not raw_text:
            # Check if it was scanned image without text layer
            logger.warning("PDF '%s' produced zero extractable text (potential scanned image)", file_name)

        return ParsedDocument(
            raw_text=raw_text,
            file_name=file_name,
            file_type="application/pdf",
            file_hash=file_hash,
            page_or_section_count=page_count,
            metadata=metadata,
        )
