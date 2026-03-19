"""FastAPI application for Sasa/Zamani — meaning-making through semantic clustering and myth generation."""

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db import check_connection, ensure_schema, get_clusters, get_events
from app.models import ClusterResponse, EventResponse, HealthResponse, MythRequest, MythResponse
from app.granola import process_granola_upload
from app.models import GranolaRequest
from app.myth import get_or_generate_myth
from app.telegram import process_telegram_update

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate settings, database schema, and seed clusters at startup."""
    get_settings()
    ensure_schema()
    _ensure_seed_clusters()
    yield


def _ensure_seed_clusters() -> None:
    """Seed clusters if not already present. Called once at startup."""
    from app.clustering import seed_clusters

    seed_clusters()


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


@app.get("/events", response_model=list[EventResponse])
async def list_events(participant: str | None = None) -> list[EventResponse]:
    """Return all events as JSON. Optionally filter by participant name."""
    rows = get_events(participant)
    return [EventResponse(**row) for row in rows]


@app.get("/clusters", response_model=list[ClusterResponse])
async def list_clusters() -> list[ClusterResponse]:
    """Return cluster definitions with archetype names."""
    rows = get_clusters()
    return [ClusterResponse(**row) for row in rows]


@app.post("/telegram")
async def telegram_webhook(request: Request) -> dict:
    """Receive Telegram webhook updates. Always returns 200 to prevent Telegram retry storms."""
    import logging

    tg_logger = logging.getLogger("app.telegram")

    try:
        body = await request.json()
    except Exception:
        return {"ok": True, "skipped": True, "reason": "invalid_json"}

    try:
        result = process_telegram_update(body)
    except Exception as exc:
        tg_logger.error("Unhandled error in telegram pipeline: %s", exc)
        return {"ok": False, "error": "internal_error"}

    if not result["processed"]:
        return {"ok": True, "skipped": True, "reason": result["reason"]}

    return {"ok": True}


@app.post("/granola")
async def granola_upload(request: Request):
    """Upload a Granola conversation transcript. Parses speaker turns, attributes participants, embeds, and stores."""
    import logging

    from fastapi.responses import JSONResponse

    granola_logger = logging.getLogger("app.granola")

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "invalid_json"})

    try:
        payload = GranolaRequest(**body)
    except Exception:
        return JSONResponse(status_code=400, content={"error": "missing_transcript_field"})

    try:
        results = process_granola_upload(payload.transcript)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})
    except Exception as exc:
        granola_logger.error("Granola pipeline failed: %s", exc)
        return JSONResponse(status_code=503, content={"error": "pipeline_failed"})

    return {"events": results}


@app.post("/myth", response_model=MythResponse)
async def generate_myth(request: MythRequest) -> MythResponse:
    """Generate a mythic sentence for a cluster via Claude. Returns cached result if fresh, regenerates if stale."""
    import logging

    from fastapi.responses import JSONResponse

    myth_logger = logging.getLogger("app.myth")

    try:
        text, is_cached = get_or_generate_myth(str(request.cluster_id))
    except ValueError:
        return JSONResponse(status_code=404, content={"error": "cluster_not_found"})
    except Exception as exc:
        myth_logger.error("Myth generation failed for cluster %s: %s", request.cluster_id, exc)
        return JSONResponse(status_code=503, content={"error": "myth_generation_failed"})

    return MythResponse(myth_text=text, cached=is_cached)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint for Railway deployment monitoring."""
    db_ok = check_connection()
    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        database="connected" if db_ok else "disconnected",
    )
