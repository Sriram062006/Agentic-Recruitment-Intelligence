"""
Abstract Base Embedding Service interface.
"""

from abc import ABC, abstractmethod
from typing import List
import numpy as np


class BaseEmbeddingService(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Returns the embedding vector dimensionality (e.g., 384)."""
        pass

    @abstractmethod
    def embed_text(self, text: str) -> np.ndarray:
        """Generates an L2-normalized 1D dense vector for a single text."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Generates L2-normalized 2D dense vectors for a batch of texts."""
        pass
