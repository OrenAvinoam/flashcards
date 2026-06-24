import uuid
from typing import Annotated, Any, Literal

from arq import create_pool
from arq.connections import RedisSettings
from arq.jobs import Job, JobStatus
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from flashcards_common.jwt import JWTUser, jwt_dependency
from generation_svc.config import get_settings
from generation_svc.worker import extract_text_from_pdf

router = APIRouter(prefix="/jobs")
_settings = get_settings()
_get_current_user = jwt_dependency(_settings.jwt_secret)
CurrentUser = Annotated[JWTUser, Depends(_get_current_user)]


def _redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(_settings.redis_url)


class GenerateResponse(BaseModel):
    job_id: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: Literal["queued", "in_progress", "complete", "not_found", "failed"]
    result: list[dict[str, str]] | None = None


@router.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_generate(
    user: CurrentUser,
    text: Annotated[str | None, Form()] = None,
    file: Annotated[UploadFile | None, File()] = None,
    count: Annotated[int, Form()] = 10,
) -> GenerateResponse:
    if text is None and file is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide either 'text' field or a PDF file upload.",
        )

    source_text: str
    if file is not None:
        raw = await file.read()
        if file.content_type == "application/pdf" or (file.filename or "").endswith(".pdf"):
            source_text = extract_text_from_pdf(raw)
        else:
            source_text = raw.decode("utf-8", errors="replace")
    else:
        source_text = text or ""

    count = max(5, min(count, 15))

    pool = await create_pool(_redis_settings())
    job = await pool.enqueue_job("generate_cards_job", source_text, count)
    await pool.aclose()

    if job is None:
        raise HTTPException(status_code=500, detail="Failed to enqueue job")

    return GenerateResponse(job_id=job.job_id)


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    user: CurrentUser,
) -> JobStatusResponse:
    pool = await create_pool(_redis_settings())
    job = Job(job_id, pool)
    job_status = await job.status()
    await pool.aclose()

    if job_status == JobStatus.not_found:
        return JobStatusResponse(job_id=job_id, status="not_found")

    if job_status in (JobStatus.queued, JobStatus.deferred):
        return JobStatusResponse(job_id=job_id, status="queued")

    if job_status == JobStatus.in_progress:
        return JobStatusResponse(job_id=job_id, status="in_progress")

    if job_status == JobStatus.complete:
        info = await job.info()
        if info and info.success:
            result: list[dict[str, str]] = info.result
            return JobStatusResponse(job_id=job_id, status="complete", result=result)
        return JobStatusResponse(job_id=job_id, status="failed")

    return JobStatusResponse(job_id=job_id, status="failed")
