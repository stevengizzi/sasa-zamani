"""Shared test fixtures for Sasa/Zamani test suite."""

from collections.abc import AsyncIterator
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set mock environment variables so tests don't require real API keys."""
    monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "fake-supabase-key")
    monkeypatch.setenv("OPENAI_API_KEY", "fake-openai-key")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-telegram-token")


@pytest.fixture
async def client(mock_env_vars: None) -> AsyncIterator[AsyncClient]:
    """Async HTTP test client for the FastAPI app."""
    # Import inside fixture so mock env vars are set before Settings loads
    from app.config import get_settings

    get_settings.cache_clear()

    from app.main import app

    # Mock DB functions so tests don't need a real Supabase connection
    with (
        patch("app.main.ensure_schema"),
        patch("app.main.check_connection", return_value=True),
        patch("app.main._ensure_seed_clusters"),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    get_settings.cache_clear()
