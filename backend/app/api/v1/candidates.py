"""
API endpoints for Candidate Pool Ingestion, Canonical Profiles, and Directory Management.
Preserves the Single-Candidate Multi-Role Model and SHA-256 Deduplication.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

from app.core.logging import get_logger
from app.core.orchestrator import PipelineOrchestrator
from app.parsers.factory import parse_document
from app.schemas.candidate import CandidateProfile, CandidateResponse
from app.services.database.repositories.candidate_repo import CandidateRepository
from app.services.embeddings.sentence_transformer import SentenceTransformerService
from app.services.llm.gemini_provider import GeminiLLMProvider
from app.services.storage.supabase_storage import SupabaseStorageService
from app.services.vector_store.faiss_store import get_faiss_store

logger = get_logger("api_candidates")
router = APIRouter(prefix="/candidates", tags=["Candidate Pool"])

candidate_repo = CandidateRepository()
storage_service = SupabaseStorageService()
llm_provider = GeminiLLMProvider()
embedding_service = SentenceTransformerService()
faiss_store = get_faiss_store()
orchestrator = PipelineOrchestrator(
    candidate_repo=candidate_repo,
    embedding_service=embedding_service,
    faiss_store=faiss_store,
    llm_provider=llm_provider,
)


@router.post(
    "/upload",
    response_model=List[CandidateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk upload and ingest candidate resumes (PDF/DOCX)",
)
async def upload_candidates(
    files: List[UploadFile] = File(..., description="Resume files in PDF or DOCX format"),
) -> List[CandidateResponse]:
    """
    Ingests resumes, enforces SHA-256 deduplication, extracts canonical profiles,
    and indexes embeddings into FAISS.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No resume files provided")

    ingested_candidates = []

    for file in files:
        file_name = file.filename or "resume.pdf"
        try:
            content = await file.read()
            if len(content) == 0:
                raise ValueError(f"Resume file '{file_name}' contains 0 bytes")

            # 1. Parse document & compute SHA-256 hash
            parsed_doc = parse_document(content, file_name)

            # 2. Check for duplicate candidate file hash (Idempotency)
            existing_candidate = candidate_repo.get_by_hash(parsed_doc.file_hash)
            if existing_candidate:
                logger.info(
                    "Resume '%s' with hash %s already exists as candidate ID %s. Returning canonical profile.",
                    file_name,
                    parsed_doc.file_hash[:8],
                    existing_candidate.id,
                )
                ingested_candidates.append(existing_candidate)
                continue

            # 3. Extract canonical structured profile via LLM provider
            profile = llm_provider.extract_candidate_profile(parsed_doc.raw_text)

            # 4. Upload file to storage
            dest_path = f"resumes/{parsed_doc.file_hash[:16]}_{file_name}"
            storage_path = storage_service.upload_file(
                bucket="resumes",
                destination_path=dest_path,
                content=content,
                content_type=parsed_doc.file_type,
            )

            # 5. Persist candidate in database
            saved_candidate = candidate_repo.create(
                file_name=file_name,
                storage_path=storage_path,
                file_hash=parsed_doc.file_hash,
                raw_text=parsed_doc.raw_text,
                structured_profile=profile,
            )

            # 6. Generate embedding & index in FAISS
            faiss_id = orchestrator.index_candidate(saved_candidate)
            saved_candidate.faiss_index_id = faiss_id

            ingested_candidates.append(saved_candidate)
            logger.info(
                "Ingested candidate '%s' (ID: %s, FAISS ID: %d)",
                profile.full_name,
                saved_candidate.id,
                faiss_id,
            )

        except ValueError as ve:
            logger.warning("Validation failure for resume '%s': %s", file_name, ve)
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            logger.error("Failed to process resume '%s': %s", file_name, e, exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error processing '{file_name}': {str(e)}")

    return ingested_candidates


@router.get(
    "",
    response_model=List[CandidateResponse],
    summary="List all canonical candidates in pool",
)
def list_candidates(
    query: Optional[str] = Query(default=None, description="Search by candidate name or skill"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> List[CandidateResponse]:
    """Lists candidates from the pool with optional search filtering."""
    candidates = candidate_repo.list_all(limit=limit, offset=offset)
    if query:
        q_lower = query.lower()
        candidates = [
            c
            for c in candidates
            if (
                q_lower in c.structured_profile.full_name.lower()
                or any(q_lower in s.lower() for s in c.structured_profile.skills)
            )
        ]
    return candidates


@router.get(
    "/{candidate_id}",
    response_model=CandidateResponse,
    summary="Get single candidate profile details",
)
def get_candidate(candidate_id: UUID) -> CandidateResponse:
    """Retrieves full canonical profile for a specific candidate."""
    cand = candidate_repo.get_by_id(candidate_id)
    if not cand:
        raise HTTPException(status_code=404, detail=f"Candidate with ID '{candidate_id}' not found")
    return cand


@router.delete(
    "/{candidate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete candidate from pool and FAISS index",
)
def delete_candidate(candidate_id: UUID) -> None:
    """Deletes a candidate from PostgreSQL and removes their vector from FAISS."""
    deleted = candidate_repo.delete(candidate_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Candidate with ID '{candidate_id}' not found")
    faiss_store.delete_candidate(candidate_id)
