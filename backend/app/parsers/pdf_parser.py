"""
PDF Document Parser using PyMuPDF (fitz/pymupdf).
Provides layout-aware extraction, spaced-letter reconstruction, and robust text sanitization.
"""

from collections import defaultdict
import hashlib
from typing import Dict, List
import fitz  # PyMuPDF

from app.core.logging import get_logger
from app.parsers.base import BaseDocumentParser, ParsedDocument
from app.parsers.sanitizer import sanitize_text

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
        page_texts: List[str] = []
        metadata: Dict[str, str] = {
            "title": str(doc.metadata.get("title") or ""),
            "author": str(doc.metadata.get("author") or ""),
        }

        for page_idx in range(page_count):
            page = doc[page_idx]
            page_text = self._extract_page_text(page)
            if page_text.strip():
                page_texts.append(page_text.strip())

        raw_combined = "\n\n".join(page_texts).strip()
        cleaned_text = sanitize_text(raw_combined)

        if not cleaned_text:
            logger.warning("PDF '%s' produced zero extractable text (potential scanned image)", file_name)

        return ParsedDocument(
            raw_text=cleaned_text,
            file_name=file_name,
            file_type="application/pdf",
            file_hash=file_hash,
            page_or_section_count=page_count,
            metadata=metadata,
        )

    def _extract_page_text(self, page: fitz.Page) -> str:
        """
        Extracts text from a page with layout-aware spaced-letter reconstruction.
        Handles stylized resumes where headings or names have intra-character spacing.
        """
        try:
            words = page.get_text("words")
            if not words:
                # Fallback to standard blocks
                blocks = page.get_text("blocks")
                text_blocks = [b[4].strip() for b in sorted(blocks, key=lambda b: (b[1], b[0])) if b[6] == 0 and b[4].strip()]
                return "\n\n".join(text_blocks)

            lines_map = defaultdict(list)
            for w in words:
                # w is (x0, y0, x1, y1, word, block_no, line_no, word_no)
                lines_map[(w[5], w[6])].append(w)

            out_lines: List[str] = []
            for key in sorted(lines_map.keys()):
                line_words = lines_map[key]
                if not line_words:
                    continue

                # Detect if line consists largely of single-character tokens (spaced letters)
                single_char_count = sum(1 for w in line_words if len(w[4]) == 1)
                is_spaced = single_char_count > len(line_words) * 0.60 and len(line_words) > 3

                if is_spaced:
                    gaps = [line_words[i + 1][0] - line_words[i][2] for i in range(len(line_words) - 1)]
                    avg_gap = sum(gaps) / len(gaps) if gaps else 0.0
                    reconstructed: List[str] = []
                    cur_w = line_words[0][4]
                    for i in range(len(line_words) - 1):
                        gap = line_words[i + 1][0] - line_words[i][2]
                        # A gap significantly larger than the average intra-character gap denotes word boundary
                        if gap > avg_gap * 1.35 and gap > 5.0:
                            reconstructed.append(cur_w)
                            cur_w = line_words[i + 1][4]
                        else:
                            cur_w += line_words[i + 1][4]
                    reconstructed.append(cur_w)
                    out_lines.append(" ".join(reconstructed))
                else:
                    out_lines.append(" ".join(w[4] for w in line_words))

            return "\n".join(out_lines)

        except Exception as e:
            logger.warning("Error during layout-aware text extraction: %s; falling back to blocks", e)
            blocks = page.get_text("blocks")
            text_blocks = [b[4].strip() for b in sorted(blocks, key=lambda b: (b[1], b[0])) if b[6] == 0 and b[4].strip()]
            return "\n\n".join(text_blocks)
