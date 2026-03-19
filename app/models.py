"""Pydantic models for request and response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EventResponse(BaseModel):
    id: UUID
    label: str
    note: str | None
    participant: str
    cluster_id: UUID | None
    created_at: datetime
    source: str
    xs: float | None = None
    day: int | None = None
    event_date: datetime | None = None


class ClusterResponse(BaseModel):
    id: UUID
    name: str
    event_count: int
    glyph_id: str | None = None
    myth_text: str | None = None
    is_seed: bool = False


class HealthResponse(BaseModel):
    status: str
    database: str


class ErrorResponse(BaseModel):
    detail: str


class GranolaRequest(BaseModel):
    transcript: str


class MythRequest(BaseModel):
    cluster_id: UUID


class MythResponse(BaseModel):
    myth_text: str
    cached: bool
