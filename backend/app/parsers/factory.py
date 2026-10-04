"""
Document Parser Factory.
Routes by file extension and provides early validation for unsupported document formats.
"""

from pathlib import Path
from typing import Dict, Type

from app.parsers.base import BaseDocumentParser, ParsedDocument
from app.parsers.docx_parser import DOCXParser
from app.parsers.pdf_parser import PDFParser

PARSERS: Dict[str, Type[BaseDocumentParser]] = {
    ".pdf": PDFParser,
    ".docx": DOCXParser,
}


def parse_document(content: bytes, file_name: str) -> ParsedDocument:
    """Parses document bytes using the appropriate parser, validating format."""
    ext = Path(file_name).suffix.lower()

    if ext not in PARSERS:
        supported = ", ".join(PARSERS.keys())
        raise ValueError(
            f"Unsupported file format '{ext}' for file '{file_name}'. Supported formats are: {supported}"
        )

    parser_cls = PARSERS[ext]
    parser = parser_cls()
    return parser.parse(content, file_name)
