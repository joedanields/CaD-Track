"""Full-pipeline test on a synthetic raster image pair (OCR path)."""
import pytest
from PIL import Image, ImageDraw, ImageFont

from app.models.diff_result import ChangeType
from app.pipeline.compare import run_comparison


def _font(size=48):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _make_image(path, labels):
    img = Image.new("L", (1600, 1200), 255)
    draw = ImageDraw.Draw(img)
    font = _font()
    for text, xy in labels:
        draw.text(xy, text, fill=0, font=font)
    img.save(path)


BASE_LABELS = [
    ("PART NUMBER 4711", (150, 150)),
    ("MATERIAL STEEL", (150, 400)),
    ("TOLERANCE 0.05", (150, 650)),
]


def test_added_label_detected(tmp_path):
    a = tmp_path / "v1.png"
    b = tmp_path / "v2.png"
    _make_image(a, BASE_LABELS)
    _make_image(b, BASE_LABELS + [("REVISED 2026", (900, 950))])
    result = run_comparison("test", a, b)

    assert result.diff.compare_mode == "text-only"
    added = [r for r in result.diff.regions if r.change_type == ChangeType.ADDED]
    # OCR splits labels into words; all added words belong to the new label
    assert added, "expected the new label to be detected"
    assert all(r.centroid[0] > 0.5 and r.centroid[1] > 0.5 for r in added)
    # the unchanged labels must not appear as changes
    non_added = [r for r in result.diff.regions if r.change_type != ChangeType.ADDED]
    assert non_added == []


def test_identical_images_report_no_changes(tmp_path):
    a = tmp_path / "v1.png"
    b = tmp_path / "v2.png"
    _make_image(a, BASE_LABELS)
    _make_image(b, BASE_LABELS)
    result = run_comparison("test", a, b)
    assert result.diff.regions == []
    assert "No significant differences" in result.summary
