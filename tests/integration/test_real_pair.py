"""Smoke test on the real sample pair (vector v1 vs low-res raster v2)."""
from conftest import SAMPLES

from app.pipeline.compare import run_comparison


def test_real_pair_completes():
    result = run_comparison(
        "real",
        SAMPLES / "real_pair" / "v1-new.pdf",
        SAMPLES / "real_pair" / "v2-new.pdf",
    )
    assert result.diff.path_a == "vector"
    assert result.diff.path_b == "raster"
    assert result.diff.compare_mode == "approx-geometry+text"
    assert result.summary
    # the v2 scan is too low-resolution for reliable OCR; the pipeline must
    # say so instead of pretending the comparison is trustworthy
    assert any(n.startswith("Warning:") for n in result.diff.notes)
