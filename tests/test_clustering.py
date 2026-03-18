"""Tests for app.clustering — cosine similarity, cluster assignment, seed archetypes."""

import logging
import math
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.clustering import (
    SEED_ARCHETYPES,
    assign_cluster,
    compute_seed_centroids,
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
# Integration tests (real DB + API keys required)
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestSeedClustersIntegration:
    def test_inserts_six_clusters(self) -> None:
        pass

    def test_idempotent(self) -> None:
        pass

    def test_get_clusters_returns_six(self) -> None:
        pass
