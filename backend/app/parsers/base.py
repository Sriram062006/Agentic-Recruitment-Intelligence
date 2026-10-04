"""
Abstract Base Parser and Parsed Document schema.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from pydantic import BaseModel, Field


class ParsedDocument(BaseModel):
    """Normalized document extraction container."""
    raw_text: str = Field(description="Extracted clean UTF-8 text")
    file_name: str
    file_type: str
    file_hash: str = Field(description="SHA-256 hash of file content for idempotency")
    page_or_section_count: int = Field(default=1)
    metadata: Dict[str, str] = Field(default_factory=dict)


class BaseDocumentParser(ABC):
    @abstractmethod
    def parse(self, content: bytes, file_name: str) -> ParsedDocument:
        """Parses raw file bytes into a clean ParsedDocument."""
        pass
