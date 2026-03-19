# Sprint 3, Session S1a: Database & Clustering Fixes

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/db.py`
   - `app/clustering.py`
   - `scripts/seed_clusters.py`
   - `tests/test_db.py`
   - `tests/test_clustering.py`
2. Run the test baseline (full suite — first session of sprint):
   ```
   python -m pytest -n auto -q
   ```
   Expected: ~125 tests, ~122 pass, ~3 skip
3. Verify you are on the correct branch: `main` (or sprint-3 branch if created)

## Objective
Fix four backend deferred items in one session: populate glyph_id on cluster insertion (DEF-016), make increment_event_count atomic (DEF-010), consolidate duplicated SEED_ARCHETYPES (DEF-011), and adjust Gate/Silence xs centers to eliminate overlap.

## Requirements

1. **In `app/db.py` — `insert_cluster()` glyph_id parameter (DEF-016):**
   Add an optional `glyph_id: str | None = None` parameter. When not None, include `"glyph_id": glyph_id` in the data dict passed to Supabase insert. When None, omit it (preserving current behavior for any callers that don't pass it).

2. **In `app/db.py` — atomic `increment_event_count()` (DEF-010):**
   Replace the current read-then-write pattern:
   ```python
   # CURRENT (non-atomic):
   row = client.table("clusters").select("event_count").eq("id", cluster_id).single().execute()
   new_count = row.data["event_count"] + 1
   client.table("clusters").update({"event_count": new_count}).eq("id", cluster_id).execute()
   ```
   With a single SQL update. Options:
   - Supabase RPC call to a Postgres function: `SELECT increment_cluster_count(cluster_id)`
   - Or use the Supabase client's raw SQL if available
   - Or, if neither is straightforward, use an UPDATE with a subquery pattern
   
   **If this requires creating a Postgres function (RPC), that is an escalation trigger.** Check whether the Supabase Python client supports `UPDATE ... SET event_count = event_count + 1` natively first. The simplest path is likely:
   ```python
   client.rpc("increment_event_count", {"cid": cluster_id}).execute()
   ```
   with a corresponding SQL function in Supabase. However, if you can achieve `event_count = event_count + 1` through the client's update API without RPC, prefer that.

3. **In `app/clustering.py` — update XS_CENTERS:**
   Change:
   ```python
   "The Gate": 0.12,
   "The Silence": 0.15,
   ```
   To:
   ```python
   "The Gate": 0.08,
   "The Silence": 0.20,
   ```
   All other centers unchanged.

4. **In `scripts/seed_clusters.py` — consolidate SEED_ARCHETYPES (DEF-011):**
   Remove the duplicated `SEED_ARCHETYPES` list (lines 6–61). Replace with:
   ```python
   from app.clustering import SEED_ARCHETYPES
   ```
   Verify the script still functions correctly (the list is identical in both locations).

5. **In `app/clustering.py` — pass glyph_id in `seed_clusters()`:**
   Update the `seed_clusters()` function to pass `glyph_id` from each archetype dict:
   ```python
   insert_cluster(name=name, centroid_embedding=centroids[name], is_seed=True, glyph_id=archetype["glyph_id"])
   ```

## Constraints
- Do NOT modify: `app/config.py`, `app/models.py`, `app/embedding.py`, `app/main.py`, `app/telegram.py`, `app/granola.py`, `app/myth.py`, `static/index.html`
- Do NOT change: any API endpoint response schemas or behavior
- Do NOT change: `insert_event` function signature
- `insert_cluster` glyph_id parameter MUST be optional with default None (backwards compatibility)

## Test Targets
After implementation:
- Existing tests: all must still pass
- New tests to write:
  1. `test_insert_cluster_with_glyph_id` — insert with glyph_id, verify it appears in the returned row
  2. `test_insert_cluster_without_glyph_id` — insert without glyph_id, verify default None behavior preserved
  3. `test_seed_clusters_populates_glyph_id` — after seed_clusters(), all 6 clusters have non-null glyph_id matching their archetype
  4. `test_increment_event_count_atomic` — increment from a known count, verify result is exactly +1
  5. `test_increment_event_count_from_zero` — increment from event_count=0, verify result is 1
  6. `test_xs_centers_gate_silence_separation` — assert `XS_CENTERS["The Gate"]` and `XS_CENTERS["The Silence"]` differ by ≥0.10
  7. `test_seed_clusters_script_imports` — verify `scripts/seed_clusters.py` can be imported without error (SEED_ARCHETYPES resolves from app/clustering)
- Minimum new test count: 7
- Test command: `python -m pytest -n auto -q`

## Definition of Done
- [ ] `insert_cluster` accepts optional glyph_id and persists it
- [ ] `seed_clusters()` passes glyph_id for all 6 archetypes
- [ ] `increment_event_count` is atomic (single SQL operation)
- [ ] `scripts/seed_clusters.py` imports SEED_ARCHETYPES from `app/clustering`
- [ ] XS_CENTERS: Gate=0.08, Silence=0.20
- [ ] All existing tests pass
- [ ] 7 new tests written and passing
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| `insert_cluster` still works without glyph_id | Existing test_db tests pass |
| `seed_clusters()` still creates all 6 clusters | Existing test_clustering tests pass |
| `increment_event_count` produces correct count | New atomic increment tests |
| XS_CENTERS still contains all 6 archetypes | `assert len(XS_CENTERS) == 6` |
| `scripts/seed_clusters.py` importable | New import test |
| No changes to endpoint behavior | Existing test_endpoints tests pass |

## Close-Out
After all work is complete, follow the close-out skill in .claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout. See the close-out skill for the
full schema and requirements.

**Write the close-out report to a file:**
docs/sprints/sprint-3/session-s1a-closeout.md

Do NOT just print the report in the terminal. Create the file, write the
full report (including the structured JSON appendix) to it, and commit it.

## Tier 2 Review (Mandatory — @reviewer Subagent)
After the close-out is written to file and committed, invoke the @reviewer
subagent to perform the Tier 2 review within this same session.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-3/review-context.md`
2. The close-out report path: `docs/sprints/sprint-3/session-s1a-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command (scoped): `python -m pytest tests/test_db.py tests/test_clustering.py -x -q`
5. Files that should NOT have been modified: `app/config.py`, `app/models.py`, `app/embedding.py`, `app/main.py`, `app/telegram.py`, `app/granola.py`, `app/myth.py`, `static/index.html`

The @reviewer will produce its review report and write it to:
docs/sprints/sprint-3/session-s1a-review.md

## Post-Review Fix Documentation
If the @reviewer reports CONCERNS and you fix the findings within this same
session, update both the close-out and review files per the standard protocol.

## Session-Specific Review Focus (for @reviewer)
1. Verify `insert_cluster` glyph_id parameter is truly optional (default None) — no existing callers should break
2. Verify atomic increment actually avoids read-then-write — check the implementation doesn't just wrap the old pattern in a try/except
3. Verify `scripts/seed_clusters.py` no longer contains a local SEED_ARCHETYPES definition
4. Verify XS_CENTERS values are exactly 0.08 and 0.20 for Gate and Silence

## Sprint-Level Regression Checklist

### Test Suite Baseline
- Pre-sprint: ~125 collected, ~122 pass, ~3 skip
- Hard floor: ≥118 pass

### Critical Invariants
- `GET /events` returns EventResponse list
- `GET /clusters` returns ClusterResponse list (now including glyph_id populated for seed clusters)
- `POST /telegram` always returns 200
- `POST /granola` returns `{"events": [...]}` on success
- `POST /myth` returns MythResponse
- `GET /health` returns HealthResponse
- Telegram pipeline happy path unbroken
- Granola pipeline happy path unbroken
- Myth generation unchanged
- insert_event unchanged
- get_events, get_clusters, get_cluster_centroids, cluster_exists unchanged

## Sprint-Level Escalation Criteria
1. Atomic increment requires schema change (Postgres function/RPC/migration) → escalate before implementing
2. Test pass count drops below 118 → investigate
3. File not in session's "Modifies" list needs changes → escalate to Work Journal
4. Deferred item fix reveals deeper architectural issue → escalate
