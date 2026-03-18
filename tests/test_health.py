"""Tests for health endpoint, frontend serving, and configuration loading."""

import pytest
from pydantic import ValidationError

pytestmark = pytest.mark.anyio


async def test_health_returns_200(client):
    response = await client.get("/health")
    assert response.status_code == 200


async def test_health_response_has_status_key(client):
    response = await client.get("/health")
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


async def test_frontend_returns_200(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


async def test_settings_load_from_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")

    from app.config import Settings

    settings = Settings()
    assert settings.supabase_url == "https://test.supabase.co"
    assert settings.supabase_key == "test-key"
    assert settings.openai_api_key == "test-openai"
    assert settings.telegram_bot_token == "test-token"
    assert settings.cluster_join_threshold == 0.3


async def test_missing_required_env_var_raises(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)

    from pydantic_settings import SettingsConfigDict

    from app.config import Settings

    # Build a subclass that skips .env file so only real env vars are checked
    class SettingsNoEnv(Settings):
        model_config = SettingsConfigDict(env_file=None)

    with pytest.raises(ValidationError):
        SettingsNoEnv()
