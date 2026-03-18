"""FastAPI application for Sasa/Zamani — meaning-making through semantic clustering and myth generation."""

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db import check_connection, ensure_schema

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate settings and database schema at startup to fail fast."""
    get_settings()
    ensure_schema()
    yield


app = FastAPI(title="Sasa/Zamani", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def serve_frontend() -> FileResponse:
    """Serve the Sasa Map frontend."""
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/events")
async def get_events(participant: str | None = None) -> list:
    """Return all events as JSON. Optionally filter by participant name."""
    return []


@app.get("/clusters")
async def get_clusters() -> list:
    """Return cluster definitions with archetype names, centroids, and myth text."""
    return []


@app.post("/telegram")
async def telegram_webhook(request: Request) -> dict:
    """Receive Telegram webhook updates. Validates, extracts event text, embeds, clusters, and stores."""
    return {"status": "ok"}


@app.post("/granola")
async def granola_upload(request: Request) -> dict:
    """Upload a Granola conversation transcript. Parses speaker turns, attributes participants, embeds, and stores."""
    return {"status": "ok"}


@app.post("/myth")
async def generate_myth(request: Request) -> dict:
    """Generate a mythic sentence for a cluster via Claude. Returns cached result if fresh, regenerates if stale."""
    return {"myth": ""}


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint for Railway deployment monitoring."""
    db_ok = check_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
    }
