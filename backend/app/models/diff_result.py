"""Unified diff schema shared by the vector and OCR extraction paths.

Everything downstream (stats, visualization, summary) consumes these models
and never needs to know which path produced them. All coordinates are
normalized to [0, 1] relative to the page/image size so that two documents
with different pixel dimensions are directly comparable — this is the core
fix for the old "whole page shifted a few pixels -> 100% changed" bug.
"""
from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field

BBox = tuple[float, float, float, float]  # x0, y0, x1, y1 normalized [0,1]
Point = tuple[float, float]


class ChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MOVED = "moved"
    MODIFIED = "modified"


class EntityKind(str, Enum):
    GEOMETRY = "geometry"  # grouped vector primitives (lines/curves/rects)
    TEXT = "text"          # a text span (vector text or OCR word/line)


class Entity(BaseModel):
    """A structured drawing element extracted from one document version."""

    id: str
    kind: EntityKind
    bbox: BBox
    centroid: Point
    # geometry entities: histogram of primitive kinds, e.g. {"l": 12, "c": 3}
    shape_signature: dict[str, int] = Field(default_factory=dict)
    # text entities: the string content
    text: Optional[str] = None
    # 1.0 for vector-extracted entities, OCR confidence (0..1) otherwise
    confidence: float = 1.0
    primitive_count: int = 0


class Region(BaseModel):
    """One detected change between the two versions."""

    id: str
    change_type: ChangeType
    kind: EntityKind
    bbox: BBox
    centroid: Point
    area_fraction: float  # bbox area / page area
    confidence: float
    label: Optional[str] = None       # e.g. "text: 'R10'" or "geometry (14 segments)"
    detail: Optional[str] = None      # e.g. "'REV B' -> 'REV C'" for modified text
    old_bbox: Optional[BBox] = None   # for moved/modified: where it was in v1


class DiffResult(BaseModel):
    job_id: str
    path_a: Literal["vector", "raster"]
    path_b: Literal["vector", "raster"]
    # which comparison mode was actually possible given the two input types
    compare_mode: Literal["geometry+text", "text-only"]
    page_width_a: float
    page_height_a: float
    page_width_b: float
    page_height_b: float
    regions: list[Region]
    entity_count_a: int
    entity_count_b: int
    notes: list[str] = Field(default_factory=list)
