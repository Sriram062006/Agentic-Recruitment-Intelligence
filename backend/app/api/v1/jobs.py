"""
API endpoints for Job Description Ingestion and Management.
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
from app.parsers.factory import parse_document
from app.schemas.job import JobProfile, JobResponse
from app.services.database.repositories.job_repo import JobRepository
from app.services.llm.gemini_provider import GeminiLLMProvider
from app.services.storage.supabase_storage import SupabaseStorageService

logger = get_logger("api_jobs")
router = APIRouter(prefix="/jobs", tags=["Job Descriptions"])

job_repo = JobRepository()
storage_service = SupabaseStorageService()
llm_provider = GeminiLLMProvider()


@router.post(
    "/upload",
    response_model=List[JobResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest one or more Job Descriptions (PDF/DOCX)",
)
async def upload_jobs(
    files: List[UploadFile] = File(..., description="Job Description documents in PDF or DOCX format"),
    user: AuthenticatedUser = Depends(require_recruiter_or_admin),
) -> List[JobResponse]:
    """Ingests job descriptions, parses text, extracts structured profiles, and persists records under recruiter ownership."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided in request")

    ingested_jobs = []

    for file in files:
        file_name = file.filename or "job_description.pdf"
        try:
            content = await file.read()
            if len(content) == 0:
                raise ValueError(f"File '{file_name}' is empty (0 bytes)")

            # 1. Parse document
            parsed_doc = parse_document(content, file_name)

            # 2. Extract structured profile via LLM provider
            job_profile = llm_provider.extract_job_profile(parsed_doc.raw_text, file_name=file_name)

            # 3. Store file in storage (isolated folder per recruiter user_id)
            dest_path = f"{user.id}/{parsed_doc.file_hash[:16]}_{file_name}"
            storage_path = storage_service.upload_file(
                bucket="job-descriptions",
                destination_path=dest_path,
                content=content,
                content_type=parsed_doc.file_type,
                token=user.token,
            )

            # 4. Save to repository with recruiter_id ownership
            saved_job = job_repo.create(
                title=job_profile.title,
                department=job_profile.department,
                storage_path=storage_path,
                raw_content=parsed_doc.raw_text,
                structured_profile=job_profile,
                recruiter_id=user.id,
                token=user.token,
            )
            ingested_jobs.append(saved_job)
            logger.info("Successfully ingested Job '%s' (ID: %s) for Recruiter %s", saved_job.title, saved_job.id, user.id)

        except ValueError as ve:
            logger.warning("Validation failure for file '%s': %s", file_name, ve)
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            logger.error("Failed to process job file '%s': %s", file_name, e, exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error processing '{file_name}': {str(e)}")

    return ingested_jobs


@router.get(
    "",
    response_model=List[JobResponse],
    summary="List all available Job Descriptions",
)
def list_jobs(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user: AuthenticatedUser = Depends(require_any_authenticated),
) -> List[JobResponse]:
    """Lists ingested job descriptions belonging to the authenticated recruiter or all jobs for admin."""
    scoped_recruiter_id = None if user.role == "admin" else user.id
    return job_repo.list_all(limit=limit, offset=offset, recruiter_id=scoped_recruiter_id, token=user.token)


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get single Job Description profile",
)
def get_job(
    job_id: UUID,
    user: AuthenticatedUser = Depends(require_any_authenticated),
) -> JobResponse:
    """Retrieves structured profile and text for a specific Job Description."""
    scoped_recruiter_id = None if user.role == "admin" else user.id
    job = job_repo.get_by_id(job_id, recruiter_id=scoped_recruiter_id, token=user.token)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job Description with ID '{job_id}' not found")
    return job


@router.get(
    "/{job_id}/file",
    summary="Download or view original Job Description file",
)
def get_job_file(
    job_id: UUID,
    user: AuthenticatedUser = Depends(require_any_authenticated),
):
    """Streams original Job Description document (PDF/DOCX) from Supabase Storage for reference."""
    scoped_recruiter_id = None if user.role == "admin" else user.id
    job = job_repo.get_by_id(job_id, recruiter_id=scoped_recruiter_id, token=user.token)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job Description with ID '{job_id}' not found")

    try:
        content = storage_service.download_file("job-descriptions", job.storage_path, token=user.token)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Job document file not found in storage for job '{job_id}'")
    except Exception as e:
        logger.error("Failed to download job document file: %s", e)
        raise HTTPException(status_code=500, detail=f"Storage retrieval error: {str(e)}")

    fname_lower = job.storage_path.lower()
    if fname_lower.endswith(".pdf"):
        media_type = "application/pdf"
    elif fname_lower.endswith(".docx"):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif fname_lower.endswith(".doc"):
        media_type = "application/msword"
    else:
        media_type = "application/octet-stream"

    filename = job.storage_path.split("/")[-1] if "/" in job.storage_path else f"{job.title}.pdf"
    from fastapi.responses import Response
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "private, max-age=3600",
        },
    )


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Job Description",
)
def delete_job(
    job_id: UUID,
    user: AuthenticatedUser = Depends(require_recruiter_or_admin),
) -> None:
    """Deletes a job description and its associated records."""
    deleted = job_repo.delete(job_id, recruiter_id=user.id, token=user.token)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Job Description with ID '{job_id}' not found")
