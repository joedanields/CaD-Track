"""Full-pipeline test on a synthetic vector PDF pair with known changes."""
import fitz
import pytest

from app.models.diff_result import ChangeType
from app.pipeline.compare import run_comparison


def _make_pdf(path, extra_line=False, label="SCALE 1:8"):
    doc = fitz.open()
    page = doc.new_page(width=600, height=400)
    # a fixed rectangle "part outline"
    page.draw_rect(fitz.Rect(100, 100, 300, 250), width=2)
    # a diagonal detail line
    page.draw_line(fitz.Point(320, 120), fitz.Point(450, 200), width=1.5)
    # a text annotation
    page.insert_text(fitz.Point(100, 320), label, fontsize=14)
    if extra_line:
        # the one known geometry change, far from everything else
        page.draw_line(fitz.Point(480, 300), fitz.Point(560, 360), width=2)
    doc.save(path)
    doc.close()


@pytest.fixture
def pdf_pair(tmp_path):
    a = tmp_path / "v1.pdf"
    b = tmp_path / "v2.pdf"
    _make_pdf(a)
    _make_pdf(b, extra_line=True)
    return a, b


def test_added_line_detected(pdf_pair):
    a, b = pdf_pair
    result = run_comparison("test", a, b)
    assert result.diff.compare_mode == "geometry+text"
    added = [r for r in result.diff.regions if r.change_type == ChangeType.ADDED]
    assert len(added) == 1
    # the added region is in the lower-right of the 600x400 page
    cx, cy = added[0].centroid
    assert cx > 2 / 3 and cy > 2 / 3
    # nothing else changed
    assert len(result.diff.regions) == 1
    assert "one" in result.summary and "lower-right" in result.summary


def test_text_change_detected(tmp_path):
    a = tmp_path / "v1.pdf"
    b = tmp_path / "v2.pdf"
    _make_pdf(a, label="SCALE 1:8")
    _make_pdf(b, label="SCALE 1:4")
    result = run_comparison("test", a, b)
    modified = [r for r in result.diff.regions if r.change_type == ChangeType.MODIFIED]
    assert len(modified) == 1
    assert modified[0].detail == "'SCALE 1:8' -> 'SCALE 1:4'"
    assert len(result.diff.regions) == 1


def test_identical_pdfs_report_no_changes(tmp_path):
    a = tmp_path / "v1.pdf"
    b = tmp_path / "v2.pdf"
    _make_pdf(a)
    _make_pdf(b)
    result = run_comparison("test", a, b)
    assert result.diff.regions == []
    assert "No significant differences" in result.summary
