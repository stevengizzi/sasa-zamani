"""Tests for app.embedding — unit tests with mocked OpenAI, integration tests with real API."""

import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.embedding import EmbeddingError, embed_text, embed_texts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_client(embeddings: list[list[float]]) -> MagicMock:
    """Build a mock OpenAI client that returns the given embedding vectors."""
    data = [
        SimpleNamespace(embedding=vec, index=i)
        for i, vec in enumerate(embeddings)
    ]
    mock_client = MagicMock()
    mock_client.embeddings.create.return_value = SimpleNamespace(data=data)
    return mock_client


def _fake_vector(dimensions: int = 1536, fill: float = 0.1) -> list[float]:
    return [fill] * dimensions


# ---------------------------------------------------------------------------
# Unit tests (mocked OpenAI client)
# ---------------------------------------------------------------------------

class TestEmbedTextUnit:
    def test_returns_list_of_1536_floats(self) -> None:
        vector = _fake_vector()
        mock_client = _make_mock_client([vector])

        result = embed_text("hello world", client=mock_client)

        assert isinstance(result, list)
        assert len(result) == 1536
        assert all(isinstance(v, float) for v in result)

    def test_raises_embedding_error_on_api_failure(self) -> None:
        from openai import OpenAIError

        mock_client = MagicMock()
        mock_client.embeddings.create.side_effect = OpenAIError("rate limit")

        with pytest.raises(EmbeddingError, match="OpenAI embedding request failed"):
            embed_text("anything", client=mock_client)

    def test_handles_empty_string(self) -> None:
        vector = _fake_vector()
        mock_client = _make_mock_client([vector])

        result = embed_text("", client=mock_client)

        assert len(result) == 1536


class TestEmbedTextsUnit:
    def test_multiple_inputs_returns_correct_count(self) -> None:
        vectors = [_fake_vector(fill=0.1), _fake_vector(fill=0.2), _fake_vector(fill=0.3)]
        mock_client = _make_mock_client(vectors)

        result = embed_texts(["a", "b", "c"], client=mock_client)

        assert len(result) == 3
        assert all(len(vec) == 1536 for vec in result)

    def test_empty_list_returns_empty_list(self) -> None:
        result = embed_texts([])

        assert result == []

    def test_raises_embedding_error_on_api_failure(self) -> None:
        from openai import OpenAIError

        mock_client = MagicMock()
        mock_client.embeddings.create.side_effect = OpenAIError("server error")

        with pytest.raises(EmbeddingError, match="OpenAI batch embedding request failed"):
            embed_texts(["a", "b"], client=mock_client)


# ---------------------------------------------------------------------------
# Integration tests (real OpenAI API key required)
# ---------------------------------------------------------------------------

_has_real_key = bool(os.environ.get("OPENAI_API_KEY_REAL"))

integration = pytest.mark.skipif(
    not _has_real_key,
    reason="Set OPENAI_API_KEY_REAL to run integration tests",
)


@integration
class TestEmbedTextIntegration:
    @pytest.fixture(autouse=True)
    def _use_real_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", os.environ["OPENAI_API_KEY_REAL"])
        from app.config import get_settings
        get_settings.cache_clear()

    def test_returns_1536_floats(self) -> None:
        from app.embedding import get_embedding_client

        client = get_embedding_client()
        result = embed_text("hello world", client=client)

        assert len(result) == 1536
        assert all(isinstance(v, float) for v in result)

    def test_different_texts_produce_different_embeddings(self) -> None:
        from app.embedding import get_embedding_client

        client = get_embedding_client()
        vec_a = embed_text("the sun rises in the east", client=client)
        vec_b = embed_text("quantum chromodynamics describes strong force", client=client)

        assert vec_a != vec_b

    def test_values_in_reasonable_range(self) -> None:
        from app.embedding import get_embedding_client

        client = get_embedding_client()
        result = embed_text("hello world", client=client)

        assert not all(v == 0.0 for v in result)
        assert not all(v == 1.0 for v in result)
        assert all(-1.0 <= v <= 1.0 for v in result)
