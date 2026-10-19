"""
FAISS Vector Store implementation using IndexFlatIP with L2-normalized vectors.
Manages bidirectional FAISS integer ID <-> Candidate UUID resolution, persistence, and atomic reload.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import UUID
import faiss
import numpy as np

from app.config import get_settings
from app.core.logging import get_logger
from app.services.vector_store.base import BaseVectorStore

logger = get_logger("faiss_store")


class FAISSVectorStore(BaseVectorStore):
    def __init__(
        self,
        dimension: int = 384,
        index_file_path: Optional[str] = None,
        mapping_file_path: Optional[str] = None,
    ):
        settings = get_settings()
        self.dimension = dimension
        self.index_path = Path(index_file_path or settings.faiss_index_path)
        self.mapping_path = Path(mapping_file_path or str(self.index_path) + ".mapping.json")

        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        # FAISS index with ID mapping wrapper that supports vector reconstruction
        self._raw_index = faiss.IndexFlatIP(self.dimension)
        self.index = faiss.IndexIDMap2(self._raw_index)

        # In-memory bidirectional mappings & vector cache
        self._id_to_uuid: Dict[int, UUID] = {}
        self._uuid_to_id: Dict[UUID, int] = {}
        self._vector_cache: Dict[UUID, np.ndarray] = {}
        self._next_faiss_id: int = 1

        # Attempt to load existing index if file exists
        if self.index_path.exists() and self.mapping_path.exists():
            try:
                self.load()
            except Exception as e:
                logger.warning("Could not load existing FAISS index, starting fresh: %s", e)

    @property
    def total_vectors(self) -> int:
        return self.index.ntotal

    def add_candidate(self, candidate_id: UUID, vector: np.ndarray) -> int:
        """Adds or updates a candidate vector in the FAISS index."""
        if candidate_id in self._uuid_to_id:
            # If candidate already exists, remove and re-insert
            faiss_id = self._uuid_to_id[candidate_id]
            self.delete_candidate(candidate_id)
        else:
            faiss_id = self._next_faiss_id
            self._next_faiss_id += 1

        v = vector.reshape(1, self.dimension).astype(np.float32)
        # Verify L2 normalization
        norm = np.linalg.norm(v)
        if norm > 0:
            v = v / norm

        ids = np.array([faiss_id], dtype=np.int64)
        self.index.add_with_ids(v, ids)

        self._id_to_uuid[faiss_id] = candidate_id
        self._uuid_to_id[candidate_id] = faiss_id
        self._vector_cache[candidate_id] = v.flatten()

        self.save()
        return faiss_id

    def batch_add(self, candidate_ids: List[UUID], vectors: np.ndarray) -> List[int]:
        """Adds a batch of candidate vectors efficiently."""
        if len(candidate_ids) == 0:
            return []

        faiss_ids = []
        for cid in candidate_ids:
            if cid in self._uuid_to_id:
                self.delete_candidate(cid)
            fid = self._next_faiss_id
            self._next_faiss_id += 1
            faiss_ids.append(fid)

        v_batch = vectors.reshape(len(candidate_ids), self.dimension).astype(np.float32)
        norms = np.linalg.norm(v_batch, axis=-1, keepdims=True)
        norms = np.where(norms == 0.0, 1e-12, norms)
        v_batch = v_batch / norms

        ids_arr = np.array(faiss_ids, dtype=np.int64)
        self.index.add_with_ids(v_batch, ids_arr)

        for fid, cid, v_single in zip(faiss_ids, candidate_ids, v_batch):
            self._id_to_uuid[fid] = cid
            self._uuid_to_id[cid] = fid
            self._vector_cache[cid] = v_single

        self.save()
        return faiss_ids

    def search_top_k(self, query_vector: np.ndarray, k: int = 10) -> List[Tuple[UUID, float]]:
        """Returns top-K candidate UUIDs and their inner product cosine similarity scores."""
        if self.index.ntotal == 0:
            return []

        q = query_vector.reshape(1, self.dimension).astype(np.float32)
        norm = np.linalg.norm(q)
        if norm > 0:
            q = q / norm

        actual_k = min(k, self.index.ntotal)
        scores, ids = self.index.search(q, actual_k)

        results = []
        for score, faiss_id in zip(scores[0], ids[0]):
            if faiss_id != -1 and faiss_id in self._id_to_uuid:
                # Cosine similarity bounded in [0.0, 1.0]
                sim = max(0.0, float(score))
                results.append((self._id_to_uuid[faiss_id], sim))
        return results

    def compute_similarity(self, candidate_id: UUID, query_vector: np.ndarray) -> float:
        """Retrieves direct cosine similarity between an indexed candidate and query vector."""
        if candidate_id not in self._uuid_to_id or self.index.ntotal == 0:
            return 0.0

        q = query_vector.flatten().astype(np.float32)
        norm = np.linalg.norm(q)
        if norm > 0:
            q = q / norm

        # 1. Check in-memory vector cache
        if candidate_id in self._vector_cache:
            cand_vec = self._vector_cache[candidate_id]
            score = float(np.dot(cand_vec, q))
            return max(0.0, min(1.0, score))

        # 2. Reconstruct from FAISS index
        faiss_id = self._uuid_to_id[candidate_id]
        try:
            cand_vec = self.index.reconstruct(faiss_id)
            score = float(np.dot(cand_vec, q))
            self._vector_cache[candidate_id] = cand_vec
            return max(0.0, min(1.0, score))
        except Exception as e:
            logger.warning("Could not reconstruct vector for candidate %s: %s", candidate_id, e)
            return 0.0

    def delete_candidate(self, candidate_id: UUID) -> bool:
        if candidate_id not in self._uuid_to_id:
            return False

        faiss_id = self._uuid_to_id[candidate_id]
        ids_to_remove = np.array([faiss_id], dtype=np.int64)
        self.index.remove_ids(ids_to_remove)

        del self._uuid_to_id[candidate_id]
        del self._id_to_uuid[faiss_id]
        self._vector_cache.pop(candidate_id, None)
        self.save()
        return True

    def save(self) -> None:
        """Persists the FAISS index binary and json mapping table."""
        try:
            faiss.write_index(self.index, str(self.index_path))
            mapping_data = {
                "next_id": self._next_faiss_id,
                "mappings": {str(fid): str(cid) for fid, cid in self._id_to_uuid.items()},
            }
            with open(self.mapping_path, "w", encoding="utf-8") as f:
                json.dump(mapping_data, f, indent=2)
            logger.debug("FAISS index saved with %d vectors", self.index.ntotal)
        except Exception as e:
            logger.error("Failed to save FAISS index: %s", e)

    def load(self) -> None:
        """Loads FAISS index and ID mapping from disk."""
        if not self.index_path.exists() or not self.mapping_path.exists():
            return

        loaded_index = faiss.read_index(str(self.index_path))

        with open(self.mapping_path, "r", encoding="utf-8") as f:
            mapping_data = json.load(f)

        if "mappings" in mapping_data:
            self._next_faiss_id = mapping_data.get("next_id", 1)
            raw_mappings = mapping_data.get("mappings", {})
        else:
            raw_mappings = mapping_data
            self._next_faiss_id = len(raw_mappings) + 1

        self._id_to_uuid = {int(k): UUID(v) for k, v in raw_mappings.items()}
        self._uuid_to_id = {UUID(v): int(k) for k, v in raw_mappings.items()}

        if not isinstance(loaded_index, (faiss.IndexIDMap, faiss.IndexIDMap2)):
            raw_flat = faiss.IndexFlatIP(self.dimension)
            new_id_map = faiss.IndexIDMap2(raw_flat)
            if loaded_index.ntotal > 0:
                ids_list = sorted(self._id_to_uuid.keys())
                if len(ids_list) == loaded_index.ntotal:
                    for i, fid in enumerate(ids_list):
                        v = loaded_index.reconstruct(i).reshape(1, -1).astype(np.float32)
                        new_id_map.add_with_ids(v, np.array([fid], dtype=np.int64))
                else:
                    for i in range(loaded_index.ntotal):
                        v = loaded_index.reconstruct(i).reshape(1, -1).astype(np.float32)
                        new_id_map.add_with_ids(v, np.array([i], dtype=np.int64))
            self.index = new_id_map
            self.save()
        else:
            self.index = loaded_index

        logger.info("Loaded FAISS index with %d vectors from %s", self.index.ntotal, self.index_path)


# Singleton factory for FAISS vector store
_faiss_instance: Optional[FAISSVectorStore] = None


def get_faiss_store() -> FAISSVectorStore:
    global _faiss_instance
    if _faiss_instance is None:
        _faiss_instance = FAISSVectorStore()
    return _faiss_instance
