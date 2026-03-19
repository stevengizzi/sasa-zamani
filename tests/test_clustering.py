"""Tests for app.clustering — cosine similarity, cluster assignment, seed archetypes."""

import logging
import math
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from dotenv import dotenv_values

from app.clustering import (
    SEED_ARCHETYPES,
    XS_CENTERS,
    assign_cluster,
    compute_seed_centroids,
    compute_xs,
    cosine_similarity,
    seed_clusters,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _unit_vector(dim: int, index: int) -> list[float]:
    """Return a unit vector with 1.0 at the given index, 0.0 elsewhere."""
    vec = [0.0] * dim
    vec[index] = 1.0
    return vec


def _fake_embedding(fill: float = 0.1, dims: int = 1536) -> list[float]:
    return [fill] * dims


# ---------------------------------------------------------------------------
# cosine_similarity
# ---------------------------------------------------------------------------

class TestCosineSimilarity:
    def test_identical_vectors_return_one(self) -> None:
        vec = [0.3, 0.5, 0.7, 0.2]
        assert cosine_similarity(vec, vec) == pytest.approx(1.0)

    def test_orthogonal_vectors_return_zero(self) -> None:
        vec_a = _unit_vector(4, 0)
        vec_b = _unit_vector(4, 1)
        assert cosine_similarity(vec_a, vec_b) == pytest.approx(0.0)

    def test_opposite_vectors_return_negative_one(self) -> None:
        vec_a = [1.0, 2.0, 3.0]
        vec_b = [-1.0, -2.0, -3.0]
        assert cosine_similarity(vec_a, vec_b) == pytest.approx(-1.0)

    def test_mismatched_lengths_raises(self) -> None:
        with pytest.raises(ValueError, match="equal length"):
            cosine_similarity([1.0, 2.0], [1.0])

    def test_empty_vectors_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            cosine_similarity([], [])

    def test_zero_vector_raises(self) -> None:
        with pytest.raises(ValueError, match="zero vectors"):
            cosine_similarity([0.0, 0.0], [1.0, 1.0])


# ---------------------------------------------------------------------------
# assign_cluster
# ---------------------------------------------------------------------------

class TestAssignCluster:
    def test_picks_highest_similarity(self) -> None:
        embedding = [1.0, 0.0, 0.0]
        centroids = [
            ("cluster-a", [0.0, 1.0, 0.0]),
            ("cluster-b", [1.0, 0.0, 0.0]),
            ("cluster-c", [0.0, 0.0, 1.0]),
        ]
        cluster_id, score = assign_cluster(embedding, centroids)
        assert cluster_id == "cluster-b"
        assert score == pytest.approx(1.0)

    def test_deterministic(self) -> None:
        embedding = [0.5, 0.5, 0.5]
        centroids = [
            ("c1", [1.0, 0.0, 0.0]),
            ("c2", [0.0, 1.0, 0.0]),
            ("c3", [0.0, 0.0, 1.0]),
        ]
        results = [assign_cluster(embedding, centroids) for _ in range(10)]
        assert all(r == results[0] for r in results)

    def test_below_threshold_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        embedding = _unit_vector(3, 0)
        centroids = [("only", _unit_vector(3, 1))]

        with caplog.at_level(logging.WARNING, logger="app.clustering"):
            cluster_id, score = assign_cluster(embedding, centroids)

        assert cluster_id == "only"
        assert score == pytest.approx(0.0)
        assert "below threshold" in caplog.text

    def test_empty_centroids_raises(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            assign_cluster([1.0], [])


# ---------------------------------------------------------------------------
# SEED_ARCHETYPES
# ---------------------------------------------------------------------------

class TestSeedArchetypes:
    EXPECTED_NAMES = {
        "The Gate",
        "What the Body Keeps",
        "The Table",
        "The Silence",
        "The Root",
        "The Hand",
    }

    def test_has_six_entries(self) -> None:
        assert len(SEED_ARCHETYPES) == 6

    def test_correct_names(self) -> None:
        names = {a["name"] for a in SEED_ARCHETYPES}
        assert names == self.EXPECTED_NAMES

    def test_all_have_required_fields(self) -> None:
        for archetype in SEED_ARCHETYPES:
            assert "name" in archetype
            assert "glyph_id" in archetype
            assert "representative_text" in archetype
            assert isinstance(archetype["representative_text"], str)
            assert len(archetype["representative_text"]) > 20


# ---------------------------------------------------------------------------
# compute_xs
# ---------------------------------------------------------------------------

class TestComputeXs:
    EXPECTED_CENTERS = {
        "The Gate": 0.08,
        "The Silence": 0.20,
        "The Hand": 0.25,
        "The Root": 0.38,
        "What the Body Keeps": 0.50,
        "The Table": 0.82,
    }

    def test_returns_correct_center_for_each_seed(self) -> None:
        for name, expected_center in self.EXPECTED_CENTERS.items():
            result = compute_xs(name, 0, 1)
            assert abs(result - expected_center) < 0.01, (
                f"{name}: expected ~{expected_center}, got {result}"
            )

    def test_unknown_cluster_defaults_to_050(self) -> None:
        result = compute_xs("Unknown Future Cluster", 0, 1)
        assert abs(result - 0.50) < 0.01

    def test_output_in_valid_range(self) -> None:
        for name in list(XS_CENTERS.keys()) + ["Unknown"]:
            for count in [1, 5, 20, 100]:
                for index in range(count):
                    result = compute_xs(name, index, count)
                    assert 0.0 <= result <= 1.0, (
                        f"Out of range for {name} idx={index} count={count}: {result}"
                    )

    def test_different_indices_produce_different_values(self) -> None:
        values = [compute_xs("The Gate", i, 5) for i in range(5)]
        assert len(set(values)) == 5, f"Expected 5 unique values, got {values}"

    def test_deterministic(self) -> None:
        results = [compute_xs("The Root", 3, 10) for _ in range(10)]
        assert all(r == results[0] for r in results)


# ---------------------------------------------------------------------------
# compute_seed_centroids (mocked embedding)
# ---------------------------------------------------------------------------

class TestComputeSeedCentroids:
    def test_returns_six_embeddings_of_correct_dim(self) -> None:
        fake_vectors = [_fake_embedding(fill=i * 0.1) for i in range(6)]

        mock_client = MagicMock()
        data = [
            SimpleNamespace(embedding=vec, index=i)
            for i, vec in enumerate(fake_vectors)
        ]
        mock_client.embeddings.create.return_value = SimpleNamespace(data=data)

        with patch("app.embedding.get_embedding_client", return_value=mock_client):
            from app.config import get_settings
            get_settings.cache_clear()
            result = compute_seed_centroids()

        assert len(result) == 6
        for name, embedding in result.items():
            assert len(embedding) == 1536
            assert all(isinstance(v, float) for v in embedding)

        expected_names = {a["name"] for a in SEED_ARCHETYPES}
        assert set(result.keys()) == expected_names


# ---------------------------------------------------------------------------
# XS_CENTERS Gate/Silence separation
# ---------------------------------------------------------------------------


class TestXsCentersGateSilenceSeparation:
    def test_gate_silence_differ_by_at_least_010(self) -> None:
        assert abs(XS_CENTERS["The Gate"] - XS_CENTERS["The Silence"]) >= 0.10


# ---------------------------------------------------------------------------
# seed_clusters passes glyph_id
# ---------------------------------------------------------------------------


class TestSeedClustersGlyphId:
    def test_seed_clusters_populates_glyph_id(self) -> None:
        fake_vectors = [_fake_embedding(fill=i * 0.1) for i in range(6)]

        mock_openai = MagicMock()
        data = [
            SimpleNamespace(embedding=vec, index=i)
            for i, vec in enumerate(fake_vectors)
        ]
        mock_openai.embeddings.create.return_value = SimpleNamespace(data=data)

        mock_db_client = MagicMock()
        # cluster_exists returns False for all (so all get inserted)
        cluster_select = mock_db_client.table("clusters").select.return_value
        cluster_select.eq.return_value.limit.return_value.execute.return_value = MagicMock(count=0)
        # insert returns a fake row
        mock_db_client.table("clusters").insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "cl-fake", "name": "fake", "glyph_id": "fake"}]
        )

        with (
            patch("app.embedding.get_embedding_client", return_value=mock_openai),
            patch("app.db.create_client", return_value=mock_db_client),
        ):
            from app.config import get_settings
            from app.db import reset_client

            get_settings.cache_clear()
            reset_client()
            seed_clusters()

        # Verify insert was called with glyph_id for each archetype
        insert_calls = mock_db_client.table("clusters").insert.call_args_list
        glyph_ids_passed = [call[0][0].get("glyph_id") for call in insert_calls]
        expected_glyph_ids = {a["glyph_id"] for a in SEED_ARCHETYPES}
        assert set(glyph_ids_passed) == expected_glyph_ids
        assert all(gid is not None for gid in glyph_ids_passed)


# ---------------------------------------------------------------------------
# seed_clusters.py script import
# ---------------------------------------------------------------------------


class TestSeedClustersScriptImport:
    def test_seed_clusters_script_imports(self) -> None:
        import scripts.seed_clusters  # noqa: F401
        assert hasattr(scripts.seed_clusters, "SEED_ARCHETYPES")
        assert scripts.seed_clusters.SEED_ARCHETYPES is SEED_ARCHETYPES


# ---------------------------------------------------------------------------
# Integration tests (real DB + API keys required)
# ---------------------------------------------------------------------------

_env_path = Path(__file__).resolve().parent.parent / ".env"
_real_env = dotenv_values(_env_path)
_has_real_credentials = bool(
    _real_env.get("OPENAI_API_KEY")
    and _real_env.get("SUPABASE_URL")
    and _real_env.get("SUPABASE_KEY")
)

EXPECTED_ARCHETYPE_NAMES = {a["name"] for a in SEED_ARCHETYPES}


@pytest.mark.integration
@pytest.mark.skipif(
    not _has_real_credentials,
    reason="Real OPENAI_API_KEY, SUPABASE_URL, and SUPABASE_KEY required in .env",
)
class TestSeedClustersIntegration:
    @pytest.fixture(autouse=True)
    def _use_real_credentials(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Override mock_env_vars with real credentials from .env."""
        monkeypatch.setenv("OPENAI_API_KEY", _real_env["OPENAI_API_KEY"])
        monkeypatch.setenv("SUPABASE_URL", _real_env["SUPABASE_URL"])
        monkeypatch.setenv("SUPABASE_KEY", _real_env["SUPABASE_KEY"])

        from app.config import get_settings
        from app.db import reset_client

        get_settings.cache_clear()
        reset_client()

        yield

        # Cleanup: delete all seed clusters, then reset singletons
        from app.db import get_db

        db = get_db()
        for name in EXPECTED_ARCHETYPE_NAMES:
            db.table("clusters").delete().eq("name", name).execute()

        reset_client()
        get_settings.cache_clear()

    def test_inserts_six_clusters(self) -> None:
        from app.db import get_clusters

        seed_clusters()
        clusters = get_clusters()
        cluster_names = {c["name"] for c in clusters}

        assert len(clusters) == 6
        assert cluster_names == EXPECTED_ARCHETYPE_NAMES

    def test_idempotent(self) -> None:
        from app.db import get_clusters

        seed_clusters()
        seed_clusters()
        clusters = get_clusters()

        assert len(clusters) == 6

    def test_get_clusters_returns_six(self) -> None:
        from app.db import get_clusters

        seed_clusters()
        clusters = get_clusters()

        assert len(clusters) == 6
        for cluster in clusters:
            assert "name" in cluster
            assert "id" in cluster
            assert "event_count" in cluster
            assert cluster["is_seed"] is True
