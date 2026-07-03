"""Load an uploaded file into a uniform InputDocument wrapper.

PDFs are opened with PyMuPDF; plain images are wrapped in a single-page
PDF-like interface by converting them to a fitz document via Pixmap, so the
rest of the pipeline only ever deals with fitz pages.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass
class InputDocument:
    path: Path
    doc: fitz.Document
    is_pdf: bool

    @property
    def page(self) -> fitz.Page:
        """First page — MVP compares page 1 of each document."""
        return self.doc[0]

    def close(self) -> None:
        self.doc.close()


def load_input(path: Path) -> InputDocument:
    ext = path.suffix.lower()
    if ext == ".pdf":
        doc = fitz.open(path)
        if doc.page_count == 0:
            doc.close()
            raise ValueError(f"PDF '{path.name}' has no pages.")
        return InputDocument(path=path, doc=doc, is_pdf=True)

    # plain image: wrap in a one-page PDF so downstream code is uniform
    img_doc = fitz.open(path)  # fitz opens images natively
    pdf_bytes = img_doc.convert_to_pdf()
    img_doc.close()
    doc = fitz.open("pdf", pdf_bytes)
    return InputDocument(path=path, doc=doc, is_pdf=False)
