"""
Abstract Base Vector Store interface.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple
from uuid import UUID
import numpy as np


class BaseVectorStore(ABC):
    @abstractmethod
    def add_candidate(self, candidate_id: UUID, vector: np.ndarray) -> int:
        """Adds a candidate vector to the index and returns the assigned FAISS integer ID."""
        pass

    @abstractmethod
    def search_top_k(self, query_vector: np.ndarray, k: int = 10) -> List[Tuple[UUID, float]]:
        """Searches index for top-K candidates closest to query vector, returning (candidate_id, similarity_score)."""
        pass

    @abstractmethod
    def delete_candidate(self, candidate_id: UUID) -> bool:
        """Removes a candidate vector from the index."""
        pass

    @abstractmethod
    def save(self) -> None:
        """Persists the vector index and ID mapping to disk."""
        pass

    @abstractmethod
    def load(self) -> None:
        """Loads index and ID mapping from disk."""
        pass
