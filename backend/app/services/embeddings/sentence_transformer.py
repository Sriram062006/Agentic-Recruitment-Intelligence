"""
Sentence Transformer Embedding Service using all-MiniLM-L6-v2 (384-dimensional).
Enforces L2 normalization for exact Inner Product (cosine-equivalent) retrieval in FAISS.
Accurately records model initialization time vs. per-inference execution time.
"""

import time
from typing import List, Optional
import numpy as np

from app.core.logging import get_logger
from app.services.embeddings.base import BaseEmbeddingService

logger = get_logger("embeddings")


class SentenceTransformerService(BaseEmbeddingService):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._dimension = 384
        self.initialization_time_seconds: float = 0.0
        self.last_inference_time_seconds: float = 0.0
        self._model = None
        self._load_model()

    def _load_model(self) -> None:
        start_t = time.perf_counter()
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading Sentence Transformer model '%s'...", self.model_name)
            self._model = SentenceTransformer(self.model_name)
            self.initialization_time_seconds = time.perf_counter() - start_t
            logger.info("Model '%s' loaded in %.3fs", self.model_name, self.initialization_time_seconds)
        except Exception as e:
            logger.error("Failed to load sentence_transformers: %s", e)
            self._model = None
            self.initialization_time_seconds = time.perf_counter() - start_t

    @property
    def dimension(self) -> int:
        return self._dimension

    def _l2_normalize(self, vectors: np.ndarray) -> np.ndarray:
        """Applies L2 unit-norm normalization across the embedding vectors."""
        norms = np.linalg.norm(vectors, axis=-1, keepdims=True)
        # Avoid division by zero on empty or zero vectors
        norms = np.where(norms == 0.0, 1e-12, norms)
        return (vectors / norms).astype(np.float32)

    def embed_text(self, text: str) -> np.ndarray:
        clean_text = text.strip() if text else "empty"
        batch_res = self.embed_batch([clean_text])
        return batch_res[0]

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        start_t = time.perf_counter()
        clean_texts = [t.strip() if (t and t.strip()) else "empty" for t in texts]

        if self._model is not None:
            raw_embeddings = self._model.encode(
                clean_texts,
                batch_size=32,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=False,
            )
            normalized = self._l2_normalize(raw_embeddings)
        else:
            # Deterministic pseudo-embedding fallback in case weights cannot be fetched from HuggingFace
            logger.warning("Using deterministic fallback embedding generator")
            vectors = []
            for t in clean_texts:
                # Seed a reproducible vector from text hash
                seed = sum(ord(c) for c in t) % (2**31 - 1)
                rng = np.random.default_rng(seed)
                v = rng.standard_normal(self._dimension)
                vectors.append(v)
            normalized = self._l2_normalize(np.array(vectors, dtype=np.float32))

        self.last_inference_time_seconds = time.perf_counter() - start_t
        return normalized
