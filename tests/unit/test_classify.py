from conftest import SAMPLES

from app.detect.classify import classify_page
from app.ingest.loader import load_input


def test_real_samples_classification():
    doc_a = load_input(SAMPLES / "real_pair" / "v1-new.pdf")
    doc_b = load_input(SAMPLES / "real_pair" / "v2-new.pdf")
    try:
        assert classify_page(doc_a.page) == "vector"
        assert classify_page(doc_b.page) == "raster"
    finally:
        doc_a.close()
        doc_b.close()
