"""Tests for the myth generation module."""

from unittest.mock import MagicMock, patch

import pytest

from app.config import get_settings
from app.myth import build_myth_prompt, generate_myth, should_regenerate


class TestBuildMythPrompt:
    def test_includes_cluster_name(self) -> None:
        prompt = build_myth_prompt("The Gate", ["dreamed of doors", "a threshold"])
        assert "The Gate" in prompt

    def test_includes_event_labels(self) -> None:
        labels = ["morning light", "bread on the table"]
        prompt = build_myth_prompt("The Table", labels)
        assert "morning light" in prompt
        assert "bread on the table" in prompt

    def test_includes_ancestral_register_instruction(self) -> None:
        prompt = build_myth_prompt("The Root", ["memory of soil"])
        assert "ancestral register" in prompt
        assert "Ancestral and exact" in prompt

    def test_includes_register_guidance(self) -> None:
        prompt = build_myth_prompt("The Root", ["memory of soil", "deep earth", "old ground"])
        assert "ancestral" in prompt
        assert "marginalia" in prompt
        assert "scholar" in prompt

    def test_thin_cluster(self) -> None:
        prompt = build_myth_prompt("The Gate", ["a single door"])
        assert "still forming" in prompt
        assert "10-20 words" in prompt

    def test_normal_cluster(self) -> None:
        labels = ["wrote a letter", "held a pen", "drew a map", "signed the page", "ink stain"]
        prompt = build_myth_prompt("The Hand", labels)
        assert "20-35 words" in prompt
        assert "still forming" not in prompt

    def test_includes_prohibited_words(self) -> None:
        prompt = build_myth_prompt("The Silence", ["quiet hours"])
        assert "journey" in prompt
        assert "transformation" in prompt
        assert "powerful" in prompt
        assert "Do NOT use these words" in prompt


class TestShouldRegenerate:
    @patch("app.myth.get_latest_myth", return_value=None)
    def test_returns_true_when_no_myth(self, mock_latest: MagicMock) -> None:
        assert should_regenerate("cluster-1", 5) is True

    @patch(
        "app.myth.get_latest_myth",
        return_value={"event_count_at_generation": 2, "version": 1},
    )
    def test_returns_true_when_delta_gte_3(self, mock_latest: MagicMock) -> None:
        assert should_regenerate("cluster-1", 6) is True

    @patch(
        "app.myth.get_latest_myth",
        return_value={"event_count_at_generation": 2, "version": 1},
    )
    def test_returns_true_when_delta_exactly_3(self, mock_latest: MagicMock) -> None:
        assert should_regenerate("cluster-1", 5) is True

    @patch(
        "app.myth.get_latest_myth",
        return_value={"event_count_at_generation": 4, "version": 1},
    )
    def test_returns_false_when_delta_lt_3(self, mock_latest: MagicMock) -> None:
        assert should_regenerate("cluster-1", 5) is False


class TestGenerateMyth:
    @patch("app.myth.get_settings")
    @patch("app.myth.anthropic.Anthropic")
    def test_returns_text_from_claude(
        self, mock_anthropic_cls: MagicMock, mock_settings: MagicMock
    ) -> None:
        mock_settings.return_value.anthropic_api_key = "fake-key"
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="The vessel remembers what the hand released.")]
        mock_client.messages.create.return_value = mock_response

        result = generate_myth("c1", "The Hand", ["wrote a letter", "held a pen"])
        assert result == "The vessel remembers what the hand released."

    @patch("app.myth.get_settings")
    @patch("app.myth.anthropic.Anthropic")
    def test_returns_fallback_on_api_error(
        self, mock_anthropic_cls: MagicMock, mock_settings: MagicMock
    ) -> None:
        mock_settings.return_value.anthropic_api_key = "fake-key"
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API error")

        result = generate_myth("c1", "The Root", ["old soil"])
        assert result == "The pattern holds."


class TestConfigAnthropicKey:
    def test_anthropic_api_key_in_settings_fields(self) -> None:
        get_settings.cache_clear()
        settings = get_settings()
        assert "anthropic_api_key" in type(settings).model_fields
        get_settings.cache_clear()

    def test_anthropic_api_key_accessible(self) -> None:
        get_settings.cache_clear()
        settings = get_settings()
        assert settings.anthropic_api_key == "fake-anthropic-key"
        get_settings.cache_clear()
