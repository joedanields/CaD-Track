"""Pydantic request/response models for the HTTP API."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel

from .diff_result import DiffResult


class UploadResponse(BaseModel):
    job_id: str
    file_a: str
    file_b: str


class RegionStat(BaseModel):
    id: str
    change_type: str
    kind: str
    location: str
    area_fraction: float
    bbox: tuple[float, float, float, float]
    label: Optional[str] = None
    detail: Optional[str] = None


class StatsSummary(BaseModel):
    total_regions: int
    added_count: int
    removed_count: int
    moved_count: int
    modified_count: int
    total_changed_area_fraction: float
    per_region: list[RegionStat]


class JobStatus(BaseModel):
    job_id: str
    status: Literal["uploaded", "processing", "done", "failed"]
    error: Optional[str] = None
    diff_result: Optional[DiffResult] = None
    stats: Optional[StatsSummary] = None
    summary: Optional[str] = None
