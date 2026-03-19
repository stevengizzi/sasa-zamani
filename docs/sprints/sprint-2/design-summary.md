# Sprint 2 Design Summary

**Sprint Goal:** Migrate the Sasa Map frontend from hardcoded mock data to live backend API data, preserving the full interaction model (both views, animated transition, panels, chained navigation). Complete the myth generation pipeline with a server-side Claude endpoint. Add participant color encoding and individual/collective toggle.

**Execution Mode:** Human-in-the-loop

**Session Breakdown:**

- **S1: Backend xs computation + API response enrichment** (score 12, medium)
  - Creates: `scripts/backfill_xs.py`
  - Modifies: `app/clustering.py`, `app/db.py`, `app/models.py`
  - Integrates: Sprint 1 cluster assignment pipeline
- **S3a: Myth module + tests** (score 13, medium)
  - Creates: `app/myth.py`
  - Modifies: `app/config.py`
  - Integrates: `app/db.py` (cluster/myth reads)
- **S3b: Myth endpoint wiring** (score 8, low)
  - Creates: —
  - Modifies: `app/main.py`, `app/models.py`
  - Integrates: `app/myth.py` → route handler
- **S2: Frontend data layer + rendering** (score 8, low)
  - Creates: —
  - Modifies: `static/index.html`
  - Integrates: `/events` (with xs), `/clusters` (with glyph_id, myth_text)
- **S2f:** Visual-review fixes — contingency, 0.5 session
- **S3c: Frontend panel adaptation** (score 8, low)
  - Creates: —
  - Modifies: `static/index.html`
  - Integrates: S2 data layer + S3b `/myth` endpoint
- **S3cf:** Visual-review fixes — contingency, 0.5 session
- **S4: Participant colors + toggle + polish** (score 5, low)
  - Creates: —
  - Modifies: `static/index.html`
  - Integrates: All prior sessions
- **S4f:** Visual-review fixes — contingency, 0.5 session

**Execution order:** S1 → S3a → S3b → S2 → S2f → S3c → S3cf → S4 → S4f

**Key Decisions:**

- xs computed server-side during cluster assignment, stored in events table. Sprint 2 uses cluster-center + offset; Sprint 4 upgrades to embedding-derived projection. Cluster xs centers: The Gate ~0.12, The Silence ~0.15, The Hand ~0.25, The Root ~0.38, What the Body Keeps ~0.50, The Table ~0.82.
- Edges use cluster co-membership in Sprint 2; Sprint 3 adds `/edges` endpoint with real embedding similarity. Frontend edge array consumes generic `{source, target, weight}` structure for forward-compatible data swap.
- Myth generation via backend `/myth` endpoint. Complete `myth.py` module (prompt construction in ancestral register, Claude API call, cache against `myths` table, regeneration trigger when event_count changes by 3+). Frontend calls `/myth` instead of direct Anthropic API.
- Individual/collective toggle: filter with opacity fade. "All" shows everything. Selected participant at full opacity, others at ~15%.
- Empty state: "The pattern is still forming" in Cormorant Garamond italic.
- Glyph mapping by `glyph_id` field from cluster response.

**Scope Boundaries:**

- IN: Frontend migration to live API data; backend xs computation; backend myth endpoint; participant colors; individual/collective toggle; empty state; both views + transition + panels + chained navigation with real data
- OUT: Zamani view; scroll/zoom/pan; mobile layout; moon nodes; new event arrival animation; Design Brief aesthetic refinement; embedding-derived xs; embedding-based edges; `/edges` endpoint; new input sources; DEF-010–014 fixes; canvas resize handling

**Regression Invariants:**

- All 90 existing passing tests continue to pass
- `/events`, `/clusters`, `/health`, `/telegram`, `/granola` endpoints unchanged (new fields additive only)
- Embedding pipeline unchanged except xs computation added at end of assignment
- Frontend: canvas architecture, both views, transition, panels, chained navigation, grain, typography, palette
- Deployment: Procfile, Railway auto-deploy, production URL

**File Scope:**

- Modify: `app/clustering.py`, `app/db.py`, `app/models.py`, `app/config.py`, `app/main.py`, `app/myth.py`, `static/index.html`
- Create: `scripts/backfill_xs.py`, `app/myth.py` (replacing stub)
- Do not modify: `app/telegram.py`, `app/granola.py`, `app/embedding.py`, `Procfile`, `scripts/init_supabase.sql`, `scripts/seed_clusters.py`

**Config Changes:**

- New: `anthropic_api_key: str` in `Settings` (env var: `ANTHROPIC_API_KEY`)

**Test Strategy:**

- S1: ~6 tests, S3a: ~6 tests, S3b: ~4 tests = ~16 new backend tests
- Frontend: visual verification checklists
- Expected: 93 → ~109+ tests

**Runner Compatibility:**

- Mode: human-in-the-loop
- Parallelizable: S1 and S3a
- Runner config: not generated

**Dependencies:**

- Sprint 1 complete, Railway deployed, seed clusters initialized
- `ANTHROPIC_API_KEY` env var set in Railway
- Test events in database for frontend visual verification

**Escalation Criteria:**

- Any session exceeds 2 compaction recovery attempts → Tier 3
- Myth quality failure (>30% therapy-speak) → RSK-002 escalation
- xs layout degenerate → reassess computation
- DEC-005 pressure (single-file unmanageable) → Tier 3

**Doc Updates Needed:**

- `project-knowledge.md`, `architecture.md`, `decision-log.md`, `dec-index.md`, `sprint-history.md`, `risk-register.md`, `roadmap.md`, `CLAUDE.md`

**Artifacts to Generate:**

1. ✅ Design Summary
2. ✅ Sprint Spec
3. ✅ Specification by Contradiction
4. ✅ Session Breakdown
5. ✅ Escalation Criteria
6. ✅ Regression Checklist
7. ✅ Doc Update Checklist
8. Review Context File
9. Implementation Prompts ×6 (S1, S3a, S3b, S2, S3c, S4)
10. Review Prompts ×6
11. Work Journal Handoff Prompt
