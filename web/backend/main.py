"""API FastAPI — point d'entrée backend (W01)."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from web.backend.routes.analyze import router as analyze_router
from web.backend.routes.game import router as game_router

STATIC_DIR = Path(__file__).resolve().parent / "static"


def _origines_cors() -> list[str]:
    origines = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]
    extra = os.getenv("ALLOWED_ORIGINS", "")
    if extra:
        origines.extend(partie.strip() for partie in extra.split(",") if partie.strip())
    return origines


app = FastAPI(
    title="Moteur d'échecs",
    description="API web pour jouer contre le moteur d'échecs.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origines_cors(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game_router)
app.include_router(analyze_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Vérification que le serveur répond."""
    return {"status": "ok"}


if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")
