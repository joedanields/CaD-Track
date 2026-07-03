"""CaD-Track backend entry point.

Run with:  uvicorn app.main:app --reload  (from the backend/ directory)
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import router

app = FastAPI(
    title="CaD-Track",
    description="Git-style change tracking for CAD drawings: structured "
    "entity diffing of vector geometry and text/annotations — no pixel diffing.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

_FRONTEND = Path(__file__).resolve().parent.parent.parent / "frontend"
if _FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=_FRONTEND / "src"), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(_FRONTEND / "index.html")
