"""
Tests for Sentence Transformers and FAISS Vector Store.
Verifies dimension 384, L2 normalization, top-K search, persistence, and UUID mapping.
"""

from uuid import uuid4
import numpy as np
import pytest

from app.services.embeddings.sentence_transformer import SentenceTransformerService
from app.services.vector_store.faiss_store import FAISSVectorStore


def test_sentence_transformer_dimensions_and_normalization():
    service = SentenceTransformerService()
    assert service.dimension == 384

    text = "Experienced Full Stack Engineer with React, TypeScript, and FastAPI skills."
    vec = service.embed_text(text)

    assert vec.shape == (384,)
    norm = np.linalg.norm(vec)
    assert abs(norm - 1.0) < 1e-4  # L2 normalized

    # Batch test
    texts = [
        "Data Engineer proficient in SQL and Spark",
        "Frontend Developer specializing in Tailwind and UI design",
    ]
    batch_vecs = service.embed_batch(texts)
    assert batch_vecs.shape == (2, 384)
    for v in batch_vecs:
        assert abs(np.linalg.norm(v) - 1.0) < 1e-4

    # Empty text test
    empty_vec = service.embed_text("")
    assert empty_vec.shape == (384,)
    assert abs(np.linalg.norm(empty_vec) - 1.0) < 1e-4


def test_faiss_vector_store_operations(tmp_path):
    index_file = str(tmp_path / "test_candidates.index")
    store = FAISSVectorStore(dimension=384, index_file_path=index_file)

    service = SentenceTransformerService()

    cid1 = uuid4()
    cid2 = uuid4()

    v1 = service.embed_text("Senior Python Developer specializing in backend APIs and microservices")
    v2 = service.embed_text("Product Manager leading cross-functional roadmaps")

    fid1 = store.add_candidate(cid1, v1)
    fid2 = store.add_candidate(cid2, v2)

    assert store.total_vectors == 2
    assert fid1 != fid2

    # Query for Python Developer
    q_vec = service.embed_text("Backend Engineer with strong Python and FastAPI")
    results = store.search_top_k(q_vec, k=2)

    assert len(results) == 2
    top_cid, top_score = results[0]
    # Python candidate should have significantly higher similarity than Product Manager
    assert top_cid == cid1
    assert top_score > results[1][1]

    # Reload test
    reloaded_store = FAISSVectorStore(dimension=384, index_file_path=index_file)
    assert reloaded_store.total_vectors == 2
    reloaded_results = reloaded_store.search_top_k(q_vec, k=1)
    assert reloaded_results[0][0] == cid1

    # Cleanup candidate
    store.delete_candidate(cid1)
    assert store.total_vectors == 1
