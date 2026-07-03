"""Central configuration for CaD-Track.

All tunable thresholds live here so the diff behaviour can be adjusted
without touching algorithm code.
"""
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    # --- storage ---
    upload_dir: Path = Path(__file__).resolve().parent.parent / "uploads"
    max_file_size_mb: int = 50
    allowed_extensions: tuple[str, ...] = (".pdf", ".png", ".jpg", ".jpeg")

    # --- page classification ---
    # a page with at least this many vector drawing objects is "vector"
    min_vector_drawings: int = 5

    # --- vector extraction / grouping ---
    # endpoints closer than this (in normalized page units, fraction of the
    # page diagonal) are considered connected when grouping primitives
    endpoint_join_tol: float = 0.004

    # --- entity matching ---
    # matched entities whose centroids differ by more than this fraction of
    # the page diagonal are classified "moved"
    match_search_radius: float = 0.05
    moved_tol: float = 0.008
    # minimum string similarity (0..1) for two text spans to be a match
    text_match_ratio: float = 0.75

    # --- OCR ---
    ocr_dpi: int = 300
    min_ocr_confidence: int = 40  # tesseract 0-100

    # --- approximate geometry tracing (raster inputs) ---
    trace_dpi: int = 150
    ink_threshold: int = 200          # gray value below which a pixel is "ink"
    hough_threshold: int = 10
    hough_line_length_frac: float = 0.01  # min segment length, fraction of max dim
    hough_line_gap: int = 3
    trace_join_tol: float = 0.008     # looser endpoint clustering for traced segments
    min_entity_span: float = 0.015    # drop traced entities smaller than this (bbox diagonal)
    trace_confidence: float = 0.8     # confidence assigned to traced entities
    # traced entities need looser thresholds than exact vector data
    approx_modified_compat: float = 0.55
    approx_moved_tol: float = 0.02

    # --- summary severity buckets (fraction of total page area changed) ---
    severity_minor: float = 0.02
    severity_moderate: float = 0.10

    # --- visualization ---
    render_dpi: int = 150
    max_summary_regions: int = 3


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
