"""
API endpoints for Candidate Pool Ingestion, Canonical Profiles, and Directory Management.
Preserves the Single-Candidate Multi-Role Model and SHA-256 Deduplication.
Secured with Supabase Authentication, RBAC, and PostgreSQL Row Level Security.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.core.auth import (
    AuthenticatedUser,
    require_any_authenticated,
    require_recruiter_or_admin,
)
from app.core.logging import get_logger
from app.core.orchestrator import PipelineOrchestrator
from app.parsers.factory import parse_document
from app.schemas.candidate import (
    CandidateContactUpdate,
    CandidateProfile,
    CandidateResponse,
)
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
    user: AuthenticatedUser = Depends(require_recruiter_or_admin),
) -> List[CandidateResponse]:
    """
    Ingests resumes, enforces SHA-256 deduplication, extracts canonical profiles,
    and indexes embeddings into FAISS under recruiter ownership.
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

            # 2. Check for duplicate candidate file hash within recruiter pool (Idempotency)
            existing_candidate = candidate_repo.get_by_hash(
                parsed_doc.file_hash, recruiter_id=user.id, token=user.token
            )
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
            profile = llm_provider.extract_candidate_profile(parsed_doc.raw_text, file_name=file_name)

            # 4. Upload file to private storage bucket organized by user_id
            dest_path = f"{user.id}/{parsed_doc.file_hash[:16]}_{file_name}"
            storage_path = storage_service.upload_file(
                bucket="resumes",
                destination_path=dest_path,
                content=content,
                content_type=parsed_doc.file_type,
                token=user.token,
            )

            # 5. Persist candidate in database with recruiter ownership
            saved_candidate = candidate_repo.create(
                file_name=file_name,
                storage_path=storage_path,
                file_hash=parsed_doc.file_hash,
                raw_text=parsed_doc.raw_text,
                structured_profile=profile,
                recruiter_id=user.id,
                token=user.token,
            )

            # 6. Generate embedding & index in FAISS
            faiss_id = orchestrator.index_candidate(saved_candidate)
            saved_candidate.faiss_index_id = faiss_id
            candidate_repo.update_faiss_id(saved_candidate.id, faiss_id, token=user.token)

            ingested_candidates.append(saved_candidate)
            logger.info(
                "Ingested candidate '%s' (ID: %s, FAISS ID: %d) for Recruiter %s",
                profile.full_name,
                saved_candidate.id,
                faiss_id,
                user.id,
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
    user: AuthenticatedUser = Depends(require_any_authenticated),
) -> List[CandidateResponse]:
    """Lists candidates in the candidate pool with search filtering and pagination."""
    candidates = candidate_repo.list_all(limit=limit, offset=offset, recruiter_id=None, token=user.token)
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
def get_candidate(
    candidate_id: UUID,
    user: AuthenticatedUser = Depends(require_any_authenticated),
) -> CandidateResponse:
    """Retrieves full canonical profile for a specific candidate."""
    cand = candidate_repo.get_by_id(candidate_id, recruiter_id=None, token=user.token)
    if not cand:
        raise HTTPException(status_code=404, detail=f"Candidate with ID '{candidate_id}' not found")
    return cand


@router.get(
    "/{candidate_id}/file",
    summary="Download or view original candidate resume file",
)
def get_candidate_file(
    candidate_id: UUID,
    user: AuthenticatedUser = Depends(require_any_authenticated),
):
    """Streams original resume document (PDF/DOCX) from Supabase Storage for reference."""
    cand = candidate_repo.get_by_id(candidate_id, recruiter_id=None, token=user.token)
    if not cand:
        raise HTTPException(status_code=404, detail=f"Candidate with ID '{candidate_id}' not found")

    try:
        content = storage_service.download_file("resumes", cand.storage_path, token=user.token)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Resume file not found in storage for candidate '{candidate_id}'")
    except Exception as e:
        logger.error("Failed to download resume file: %s", e)
        raise HTTPException(status_code=500, detail=f"Storage retrieval error: {str(e)}")

    fname_lower = cand.file_name.lower()
    if fname_lower.endswith(".pdf"):
        media_type = "application/pdf"
    elif fname_lower.endswith(".docx"):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif fname_lower.endswith(".doc"):
        media_type = "application/msword"
    else:
        media_type = "application/octet-stream"

    from fastapi.responses import Response
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'inline; filename="{cand.file_name}"',
            "Cache-Control": "private, max-age=3600",
        },
    )


@router.patch(
    "/{candidate_id}/contact",
    response_model=CandidateResponse,
    summary="Update candidate contact information (Name, Phone, Email, Location ONLY)",
)
def update_candidate_contact(
    candidate_id: UUID,
    contact_update: CandidateContactUpdate,
    user: AuthenticatedUser = Depends(require_recruiter_or_admin),
) -> CandidateResponse:
    """
    Updates editable contact information (Full Name, Email, Phone, Location) for a candidate.
    Strictly preserves professional career history, skills, education, and FAISS vector index.
    Protected by RBAC: Admin and Recruiter only (Viewers rejected with 403 Forbidden).
    """
    updated = candidate_repo.update_contact_info(
        candidate_id=candidate_id,
        contact_update=contact_update,
        recruiter_id=None,
        token=user.token,
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Candidate with ID '{candidate_id}' not found")
    logger.info("Updated contact details for candidate ID %s by user %s", candidate_id, user.id)
    return updated


@router.delete(
    "/{candidate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete candidate from pool and FAISS index",
)
def delete_candidate(
    candidate_id: UUID,
    user: AuthenticatedUser = Depends(require_recruiter_or_admin),
) -> None:
    """Deletes a candidate from PostgreSQL and removes their vector from FAISS."""
    deleted = candidate_repo.delete(candidate_id, recruiter_id=user.id, token=user.token)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Candidate with ID '{candidate_id}' not found")
    faiss_store.delete_candidate(candidate_id)

