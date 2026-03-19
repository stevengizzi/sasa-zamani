# Sprint 3.5 Design Summary

**Sprint Goal:** Replace speaker-turn splitting with Claude-powered thematic segmentation for transcript ingestion (both batch and live). Generate LLM labels for all event types. Add `participants` array to events schema. Re-seed production with improved data.

**Session Breakdown:**
- S1a: Thematic segmentation engine — new module with Claude-based transcript segmentation that returns `[{text, label, participants}]` segments
  - Creates: `app/segmentation.py`, `tests/test_segmentation.py`
  - Modifies: none
  - Integrates: N/A (first session)
- S1b: Schema integration — add `participants` jsonb column, update db/models layer
  - Creates: none
  - Modifies: `app/db.py`, `app/models.py`, `scripts/init_supabase.sql`, `tests/test_db.py`
  - Integrates: N/A (schema layer, consumed by S2a)
- S2a: Granola + seed_transcript pipeline integration — replace speaker-turn parsing with thematic segmentation
  - Creates: none
  - Modifies: `app/granola.py`, `scripts/seed_transcript.py`, `tests/test_granola.py`, `tests/test_seed_transcript.py`
  - Integrates: S1a's `app/segmentation.py` into granola.py and seed_transcript.py
- S2b: Telegram label generation — add Claude-generated 3-5 word labels for Telegram events
  - Creates: none
  - Modifies: `app/telegram.py`, `tests/test_telegram.py`
  - Integrates: S1a's label generation pattern (or shared utility)
- S3: Re-seed production + label backfill + verification
  - Creates: `scripts/backfill_labels.py`
  - Modifies: none (manual operations)
  - Integrates: S2a's updated seed_transcript.py against production

**Dependency chain:** S1a → S1b → S2a → S2b → S3
Manual step between S1a and S1b: add `participants` column in Supabase SQL editor.

**Key Decisions:**
- DEC-017: Multi-participant events stored as `participant = "shared"` + `participants` jsonb array preserving specific attribution
- DEC-018: Thematic segmentation applies to both `scripts/seed_transcript.py` (batch) and `app/granola.py` (live upload)
- DEC-019: Segmentation prompt produces both thematic segments and 3-5 word labels in a single Claude call (no separate label API call for transcript events)
- Telegram events get a separate small Claude call for label generation (no segmentation needed — single messages)
- Segmentation uses claude-sonnet-4-20250514 (cost management, consistent with myth.py pattern)
- Claude API failure during segmentation fails the upload (no silent fallback to speaker-turn splitting)
- Telegram label failure falls back to `text[:80]` (label is non-critical, event insertion must not be blocked)
- Zero-speaker segments default to `participant = "shared"`, `participants: []`

**Scope Boundaries:**
- IN: `participants` schema column, thematic segmentation engine, granola.py rewrite, seed_transcript.py rewrite, Telegram label generation, production re-seed, backfill 2 existing Telegram event labels
- OUT: Dynamic clustering / centroid recomputation, myth post-validation (DEF-017), transcript dedup (DEF-018), frontend changes for `participants` display, resonance/strata view changes, myth pipeline changes, mobile layout

**Regression Invariants:**
- Existing Telegram pipeline continues to insert events (with new labels, fallback to text[:80] on failure)
- `/events` and `/clusters` endpoints return valid data
- Frontend renders both views correctly (no frontend changes)
- Myth generation pipeline completely untouched
- `insert_event()` backward compatible (participants defaults to None)
- Test count stays above 118 floor
- Dry-run mode still works in seed_transcript.py

**File Scope:**
- Create: `app/segmentation.py`, `tests/test_segmentation.py`, `scripts/backfill_labels.py`
- Modify: `app/db.py`, `app/models.py`, `app/granola.py`, `app/telegram.py`, `scripts/seed_transcript.py`, `scripts/init_supabase.sql`, `tests/test_db.py`, `tests/test_granola.py`, `tests/test_telegram.py`, `tests/test_seed_transcript.py`
- Do not modify: `app/config.py`, `app/embedding.py`, `app/myth.py`, `app/clustering.py`, `app/main.py`, `static/index.html`, `tests/conftest.py`, `tests/test_myth.py`, `tests/test_clustering.py`, `tests/test_endpoints.py`

**Config Changes:** No config changes. Claude model for segmentation hardcoded in `app/segmentation.py`.

**Test Strategy:**
- S1a: ~6 new tests (segmentation parsing, multi-speaker attribution, label generation, error handling, edge cases)
- S1b: ~3 new tests (insert_event with participants, EventResponse with participants, backward compat)
- S2a: ~5 new tests (granola thematic integration, seed_transcript thematic integration, participant assignment)
- S2b: ~3 new tests (Telegram label generation, fallback on failure, label content)
- S3: ~1 new test (backfill script)
- Estimated total: ~18 new tests
- Current baseline: 147 pass, 3 skip
- Target: ~165 pass, ≤3 skip

**Runner Compatibility:**
- Mode: Human-in-the-loop
- Parallelizable sessions: none (strict linear dependency)
- S3 requires manual Supabase operations and human judgment on segmentation quality

**Dependencies:**
- Manual Supabase SQL step between S1a and S1b: `ALTER TABLE events ADD COLUMN participants jsonb DEFAULT '[]'`
- ANTHROPIC_API_KEY in environment for segmentation calls
- Existing seeded data will be deleted during S3

**Escalation Criteria:**
- Thematic segmentation produces < 50% of speaker-turn count (segments too coarse — losing too much detail)
- Thematic segmentation produces > 150% of speaker-turn count (segments too fine — not actually grouping thematically)
- Claude API cost per transcript exceeds $0.50 (prompt too large or too many calls)
- Test pass count drops below 118
- Segmentation output fails to attribute speakers correctly on manual review

**Doc Updates Needed:**
- `docs/project-knowledge.md` — updated event counts, new module, decisions
- `docs/architecture.md` — segmentation module, participants column, updated pipeline diagram
- `docs/decision-log.md` — DEC-017, DEC-018, DEC-019
- `docs/dec-index.md` — new entries
- `docs/sprint-history.md` — Sprint 3.5 entry
- `docs/roadmap.md` — DEF-019/FF-005 resolved, FF-002 resolved
- `CLAUDE.md` — updated file structure, deferred items

**Artifacts to Generate:**
1. Sprint Spec
2. Specification by Contradiction
3. Session Breakdown (with Creates/Modifies/Integrates per session)
4. Implementation Prompt x5 (S1a, S1b, S2a, S2b, S3)
5. Review Prompt x5
6. Escalation Criteria
7. Regression Checklist
8. Doc Update Checklist
9. Review Context File
10. Work Journal Handoff Prompt
