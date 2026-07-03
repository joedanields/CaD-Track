"""Bucket total changed-area fraction into a severity word."""
from __future__ import annotations

from ..config import settings


def bucket_severity(area_fraction: float) -> str:
    if area_fraction < settings.severity_minor:
        return "minor"
    if area_fraction < settings.severity_moderate:
        return "moderate"
    return "significant"
