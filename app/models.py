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


class ClusterResponse(BaseModel):
    id: UUID
    name: str
    event_count: int


class HealthResponse(BaseModel):
    status: str
    database: str


class ErrorResponse(BaseModel):
    detail: str


class GranolaRequest(BaseModel):
    transcript: str
