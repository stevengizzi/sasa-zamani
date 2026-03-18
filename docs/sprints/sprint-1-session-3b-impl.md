# Sprint 1, Session 3b: Cluster Assignment + Seed Clusters

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/embedding.py`
   - `app/db.py`
   - `app/models.py`
   - `app/config.py`
2. Run the test baseline:
   Scoped: `python -m pytest tests/test_embedding.py tests/test_db.py -x -q`
   Expected: ~17 tests, all passing (excluding integration-marked tests)
3. Verify you are on the correct branch: `sprint-1` (or `main`)

## Objective
Implement cluster assignment via cosine similarity, compute seed cluster centroids from representative archetype text using the embedding pipeline, and insert the six seed clusters into the database.

## Requirements

1. **Implement `app/clustering.py`** — the file exists as a docstring-only stub. Replace its contents with:
   - `cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float`:
     - Pure math, no external dependencies
     - Returns value between -1 and 1
   - `assign_cluster(embedding: list[float], centroids: list[tuple[str, list[float]]]) -> tuple[str, float]`:
     - Takes an event embedding and a list of (cluster_id, centroid_embedding) pairs
     - Returns (best_cluster_id, similarity_score)
     - If best similarity is below `settings.cluster_join_threshold`, log a warning but still return the best match
   - `SEED_ARCHETYPES` — **use the data from `scripts/seed_clusters.py`** as the authoritative source. That file already defines all 6 archetypes with representative text, glyph_id, and tags. Either import from it or copy the data, but preserve the glyph_id and representative_text fields exactly. The representative text in the script uses evocative sentences (better for embedding quality) rather than keywords:
     ```python
     # From scripts/seed_clusters.py — DO NOT use simplified keyword versions
     # Example: "A dream about crossing a threshold. The door that appears when you are
     #           ready to leave. Migration, departure, the moment before."
     # NOT: "dreams, thresholds, migration, crossing over, departure, arrival"
     ```
   - `compute_seed_centroids() -> dict[str, list[float]]`:
     - Embeds each archetype's representative text using `embed_text()` or `embed_texts()`
     - Returns {name: centroid_embedding} dict
   - `seed_clusters(db_client) -> None`:
     - Calls `compute_seed_centroids()`
     - Inserts each into the clusters table via `db.insert_cluster(name, centroid)`
     - Idempotent: skips insertion if cluster with that name already exists

2. Update `app/db.py`:
   - Add `cluster_exists(name: str) -> bool` function (for idempotent seeding)
   - If not already present, add any helper needed for the seeding process

3. Create `tests/test_clustering.py`:
   - Test cosine_similarity of identical vectors returns 1.0
   - Test cosine_similarity of orthogonal vectors returns 0.0
   - Test cosine_similarity of opposite vectors returns -1.0
   - Test assign_cluster picks the cluster with highest similarity
   - Test assign_cluster is deterministic (same input → same output)
   - Test assign_cluster with below-threshold similarity still returns a result (logs warning)
   - Test SEED_ARCHETYPES has exactly 6 entries with correct names
   - Test compute_seed_centroids returns 6 embeddings of 1536 dims each (mocked embedding)

   **Live seed test (integration):**
   - Mark with `@pytest.mark.integration`
   - Test seed_clusters inserts 6 clusters into DB
   - Test seed_clusters is idempotent (second call doesn't duplicate)
   - Test GET /clusters returns 6 clusters after seeding

## Constraints
- Do NOT modify: `static/index.html`, any files under `docs/`
- Do NOT modify: `app/embedding.py` (only import and call it)
- Do NOT modify: `app/main.py` (no new endpoints in this session)
- Do NOT create: dynamic cluster creation, splitting, or merging logic
- Do NOT recompute centroids after events are assigned — centroids are static seed values
- The representative text for each archetype is defined in `scripts/seed_clusters.py` — use that as the source of truth, not the simplified keyword versions originally in this prompt

## Test Targets
After implementation:
- Existing tests: all must still pass
- New tests to write: listed in Requirements #3
- Minimum new test count: 8
- Test command: `python -m pytest -x -q`

## Definition of Done
- [ ] cosine_similarity function works correctly for identical, orthogonal, and opposite vectors
- [ ] assign_cluster picks highest-similarity cluster deterministically
- [ ] All six seed archetypes defined with representative text
- [ ] compute_seed_centroids produces real embeddings (tested with mocks + one live test)
- [ ] seed_clusters inserts all 6 into DB and is idempotent
- [ ] GET /clusters returns 6 clusters after seeding
- [ ] All existing tests still pass
- [ ] All new tests pass
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Sprint-Level)
| Check | How to Verify |
|-------|---------------|
| Health endpoint returns 200 with DB status | `pytest tests/test_health.py` |
| GET /events returns valid JSON on empty DB | `pytest tests/test_endpoints.py -k "events and empty"` |
| GET /clusters returns exactly 6 seed clusters | `pytest tests/test_clustering.py -k seed` |
| Embedding module unchanged | `pytest tests/test_embedding.py` |
| Seed centroids are non-null, non-zero, 1536-dim | Check in seed test |

## Sprint-Level Escalation Criteria
1. Supabase pgvector unavailable → STOP
2. Railway deployment fails 3+ consecutive times → STOP
3. OpenAI embedding dimensions ≠ 1536 → STOP
4. **Degenerate cluster assignment (>80% to one cluster) → STOP** (directly relevant)
5. **Cosine similarity uniformly > 0.95 or < 0.1 → STOP** (directly relevant)
6. Any session exceeds 2× estimated test count → STOP
7. supabase-py requires >20 lines raw SQL for vector ops → escalate
8. Telegram webhook needs different endpoint structure → escalate
9. Compaction in Session 4b → partial close-out + follow-up

## Close-Out
After all work is complete, follow the close-out skill in .claude/workflow/claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

**Write the close-out report to a file:**
docs/sprints/sprint-1/session-3b-closeout.md

**Important for this session's close-out:** Include the similarity scores between all pairs of seed cluster centroids. This data is critical for evaluating RSK-001 (embedding quality) and escalation criteria #4/#5. Format as a matrix or table.

## Tier 2 Review (Mandatory — @reviewer Subagent)
Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-1/review-context.md`
2. The close-out report path: `docs/sprints/sprint-1/session-3b-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command: `python -m pytest tests/test_clustering.py -x -q`
5. Files that should NOT have been modified: `static/index.html`, `app/embedding.py`, `app/main.py`, anything under `docs/` (except sprint reports)

The @reviewer will write its report to: docs/sprints/sprint-1/session-3b-review.md

## Session-Specific Review Focus (for @reviewer)
1. Verify SEED_ARCHETYPES has exactly 6 entries matching the spec names
2. Verify cosine_similarity is a pure math function (no external deps)
3. Verify assign_cluster returns nearest cluster even below threshold (logs, doesn't error)
4. Verify seed_clusters is idempotent (check for cluster_exists guard)
5. Verify centroid similarity matrix in close-out — check for degenerate cases (escalation #4, #5)
6. Verify representative text matches the spec exactly (no modifications)
7. Check that clustering.py imports embedding.py (not the other way around) — dependency flows one way
