"""HTTP API endpoints."""
from __future__ import annotations

import shutil

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import Response

from ..config import settings
from ..ingest.loader import load_input
from ..ingest.validate import ValidationError, validate_upload
from ..jobs.store import store
from ..models.schemas import JobStatus, UploadResponse
from ..pipeline.compare import run_comparison
from ..viz.render import render_bbox_overlay, render_original, render_side_by_side

router = APIRouter(prefix="/api")


@router.post("/upload", response_model=UploadResponse)
async def upload(file_a: UploadFile, file_b: UploadFile) -> UploadResponse:
    saved = []
    for tag, f in (("a", file_a), ("b", file_b)):
        data = await f.read()
        try:
            ext = validate_upload(f.filename or f"file_{tag}", data)
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        saved.append((tag, data, ext))

    job = store.create(file_a=settings.upload_dir / "pending_a", file_b=settings.upload_dir / "pending_b")
    job_dir = settings.upload_dir / job.job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    for tag, data, ext in saved:
        path = job_dir / f"{tag}{ext}"
        path.write_bytes(data)
        if tag == "a":
            job.file_a = path
        else:
            job.file_b = path
    return UploadResponse(job_id=job.job_id, file_a=job.file_a.name, file_b=job.file_b.name)


@router.post("/compare/{job_id}", response_model=JobStatus)
def compare(job_id: str) -> JobStatus:
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job id")
    job.status = "processing"
    try:
        result = run_comparison(job.job_id, job.file_a, job.file_b)
        job.diff = result.diff
        job.stats = result.stats
        job.summary = result.summary
        job.status = "done"
    except Exception as exc:  # surface pipeline failures to the client
        job.status = "failed"
        job.error = str(exc)
    return _job_status(job_id)


@router.get("/jobs/{job_id}", response_model=JobStatus)
def job_status(job_id: str) -> JobStatus:
    return _job_status(job_id)


def _job_status(job_id: str) -> JobStatus:
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job id")
    return JobStatus(
        job_id=job.job_id,
        status=job.status,  # type: ignore[arg-type]
        error=job.error,
        diff_result=job.diff,
        stats=job.stats,
        summary=job.summary,
    )


@router.get("/jobs/{job_id}/summary")
def get_summary(job_id: str) -> dict:
    job = _require_done(job_id)
    return {"summary": job.summary}


@router.get("/jobs/{job_id}/stats")
def get_stats(job_id: str):
    return _require_done(job_id).stats


@router.get("/jobs/{job_id}/visualization")
def visualization(job_id: str, mode: str = "bbox") -> Response:
    job = _require_done(job_id)
    doc_a = load_input(job.file_a)
    doc_b = load_input(job.file_b)
    try:
        if mode == "bbox":
            png = render_bbox_overlay(doc_b.page, job.diff)
        elif mode == "side_by_side":
            png = render_side_by_side(doc_a.page, doc_b.page, job.diff)
        elif mode == "original_a":
            png = render_original(doc_a.page)
        elif mode == "original_b":
            png = render_original(doc_b.page)
        else:
            raise HTTPException(
                status_code=400,
                detail="mode must be one of: bbox, side_by_side, original_a, original_b",
            )
    finally:
        doc_a.close()
        doc_b.close()
    return Response(content=png, media_type="image/png")


@router.delete("/jobs/{job_id}")
def delete_job(job_id: str) -> dict:
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job id")
    shutil.rmtree(settings.upload_dir / job_id, ignore_errors=True)
    store.delete(job_id)
    return {"deleted": job_id}


def _require_done(job_id: str):
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job id")
    if job.status != "done":
        raise HTTPException(status_code=409, detail=f"Job status is '{job.status}', not 'done'")
    return job
