"""In-memory job store (MVP). Swap for SQLite if persistence is needed."""
from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..models.schemas import StatsSummary
from ..models.diff_result import DiffResult


@dataclass
class Job:
    job_id: str
    file_a: Path
    file_b: Path
    status: str = "uploaded"  # uploaded | processing | done | failed
    error: Optional[str] = None
    diff: Optional[DiffResult] = None
    stats: Optional[StatsSummary] = None
    summary: Optional[str] = None


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(self, file_a: Path, file_b: Path) -> Job:
        job = Job(job_id=uuid.uuid4().hex[:16], file_a=file_a, file_b=file_b)
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def delete(self, job_id: str) -> bool:
        with self._lock:
            return self._jobs.pop(job_id, None) is not None


store = JobStore()
