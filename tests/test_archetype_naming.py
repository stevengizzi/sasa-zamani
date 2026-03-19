"""Tests for app.archetype_naming — archetype name generation and deferred naming."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.archetype_naming import (
    ARCHETYPE_NAMING_PROMPT,
    ArchetypeNamingError,
    generate_archetype_name,
    maybe_name_cluster,
)


# ---------------------------------------------------------------------------
# generate_archetype_name
# ---------------------------------------------------------------------------


class TestGenerateArchetypeName:
    def test_returns_string(self) -> None:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = SimpleNamespace(
            content=[SimpleNamespace(text="The Vessel")]
        )

        with patch("app.archetype_naming.anthropic.Anthropic", return_value=mock_client):
            result = generate_archetype_name(
                event_labels=["morning ritual", "quiet observation"],
                event_notes=["woke early", "watched the river"],
            )

        assert isinstance(result, str)
        assert result == "The Vessel"

    def test_raises_on_api_failure(self) -> None:
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API down")

        with (
            patch("app.archetype_naming.anthropic.Anthropic", return_value=mock_client),
            pytest.raises(ArchetypeNamingError, match="Archetype naming failed"),
        ):
            generate_archetype_name(
                event_labels=["test"], event_notes=["test note"]
            )

    def test_raises_on_empty_response(self) -> None:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = SimpleNamespace(
            content=[SimpleNamespace(text="   ")]
        )

        with (
            patch("app.archetype_naming.anthropic.Anthropic", return_value=mock_client),
            pytest.raises(ArchetypeNamingError, match="Empty response"),
        ):
            generate_archetype_name(
                event_labels=["test"], event_notes=["test note"]
            )


class TestArchetypeNamingPrompt:
    def test_contains_prohibited_words(self) -> None:
        prohibited = [
            "journey", "transformation", "growth", "powerful", "explore",
            "reflect", "synchronicity", "discover", "reveal", "activation",
            "detect", "collective unconscious", "universe", "field", "signal",
        ]
        for word in prohibited:
            assert word in ARCHETYPE_NAMING_PROMPT, (
                f"Prohibited word '{word}' missing from prompt"
            )

    def test_contains_format_placeholders(self) -> None:
        assert "{labels}" in ARCHETYPE_NAMING_PROMPT
        assert "{notes}" in ARCHETYPE_NAMING_PROMPT


# ---------------------------------------------------------------------------
# maybe_name_cluster
# ---------------------------------------------------------------------------


class TestMaybeNameCluster:
    def test_names_when_eligible(self) -> None:
        cluster = {
            "id": "cl-1",
            "name": "The Unnamed",
            "event_count": 3,
            "is_seed": False,
        }

        with (
            patch("app.archetype_naming.get_cluster_by_id", return_value=cluster),
            patch("app.archetype_naming.get_cluster_events_labels", return_value=["a", "b", "c"]),
            patch("app.archetype_naming.get_cluster_events_notes", return_value=["n1", "n2", "n3"]),
            patch("app.archetype_naming.generate_archetype_name", return_value="The Hearth"),
            patch("app.archetype_naming.update_cluster_name") as mock_update,
        ):
            result = maybe_name_cluster("cl-1")

        assert result == "The Hearth"
        mock_update.assert_called_once_with("cl-1", "The Hearth")

    def test_noop_when_below_threshold(self) -> None:
        cluster = {
            "id": "cl-2",
            "name": "The Unnamed",
            "event_count": 2,
            "is_seed": False,
        }

        with patch("app.archetype_naming.get_cluster_by_id", return_value=cluster):
            result = maybe_name_cluster("cl-2")

        assert result is None

    def test_noop_when_already_named(self) -> None:
        cluster = {
            "id": "cl-3",
            "name": "The Gate",
            "event_count": 10,
            "is_seed": True,
        }

        with patch("app.archetype_naming.get_cluster_by_id", return_value=cluster):
            result = maybe_name_cluster("cl-3")

        assert result is None

    def test_handles_api_failure_gracefully(self) -> None:
        cluster = {
            "id": "cl-4",
            "name": "The Unnamed",
            "event_count": 5,
            "is_seed": False,
        }

        with (
            patch("app.archetype_naming.get_cluster_by_id", return_value=cluster),
            patch("app.archetype_naming.get_cluster_events_labels", return_value=["a", "b", "c"]),
            patch("app.archetype_naming.get_cluster_events_notes", return_value=["n1", "n2", "n3"]),
            patch(
                "app.archetype_naming.generate_archetype_name",
                side_effect=ArchetypeNamingError("API down"),
            ),
        ):
            result = maybe_name_cluster("cl-4")

        assert result is None

    def test_noop_when_cluster_not_found(self) -> None:
        with patch("app.archetype_naming.get_cluster_by_id", return_value=None):
            result = maybe_name_cluster("nonexistent")

        assert result is None
