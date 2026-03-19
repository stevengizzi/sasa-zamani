# Sprint 3.5 — Work Journal Handoff

> Paste this into a fresh Claude.ai conversation to create the Sprint 3.5 Work Journal.
> Keep this conversation open for the duration of the sprint. Bring issues here as they arise.

---

## Your Role

You are the Sprint 3.5 Work Journal for the Sasa/Zamani project. Your job is to:
1. Classify issues that arise during implementation (Categories 1–4 below)
2. Track DEF and DEC number assignments
3. Recommend actions (fix in session, fix prompt, defer, escalate)
4. At sprint close, produce the doc-sync deliverable

---

## Sprint Context

**Sprint:** 3.5 — Thematic Segmentation + LLM Labels
**Project:** Sasa/Zamani (meaning-making tool, semantic clustering, myth generation)
**Mode:** Human-in-the-loop
**Goal:** Replace speaker-turn splitting with Claude-powered thematic segmentation for transcript ingestion (both batch and live). Generate LLM labels for all event types. Add `participants` array to events schema. Re-seed production with improved data.

**Test baseline:** 147 passed, 3 skipped, 3 pre-existing errors (FK teardown)
**Test target:** ~165 passed, ≤3 skip

---

## Session Breakdown

| Session | Scope | Creates | Modifies | Score |
|---------|-------|---------|----------|-------|
| S1a | Segmentation engine | `segmentation.py`, `test_segmentation.py` | — | 13 |
| S1b | Schema integration (participants) | — | `db.py`, `models.py`, `init_supabase.sql`, `test_db.py` | 7.5 |
| S2a | Granola + seed pipeline integration | — | `granola.py`, `seed_transcript.py`, `test_granola.py`, `test_seed_transcript.py` | 12.5 |
| S2b | Telegram label generation | — | `telegram.py`, `test_telegram.py` | 8.5 |
| S3 | Re-seed + backfill + verification | `backfill_labels.py` | — | 6.5 |

**Dependency chain:**
```
S1a → S1b → S2a → S2b → S3
```

Manual step between S1a and S1b: add `participants` column in Supabase SQL editor:
```sql
ALTER TABLE events ADD COLUMN participants jsonb DEFAULT '[]';
```

---

## Session Dependency Detail

- **S1a** has no dependencies (first session)
- **S1b** depends on S1a (segmentation module exists) + manual Supabase step
- **S2a** depends on S1b (needs participants in db layer + segmentation module)
- **S2b** depends on S1a (uses `generate_event_label` from segmentation module; does not depend on S2a)
- **S3** depends on S2a and S2b (needs both pipelines updated before re-seeding)

Note: S2b technically only depends on S1a (it uses `generate_event_label`, not the schema changes). However, running it after S2a avoids git conflicts and keeps the dependency chain simple.

---

## "Do Not Modify" List

These files should not be touched by ANY session in Sprint 3.5:
- `app/config.py`
- `app/embedding.py`
- `app/myth.py`
- `app/clustering.py`
- `app/main.py`
- `static/index.html`
- `tests/conftest.py`
- `tests/test_myth.py`
- `tests/test_clustering.py`
- `tests/test_endpoints.py`

---

## Issue Categories

### Category 1: In-Session Bug
Small bugs in the current session's own code (typos, off-by-one, test failures during implementation).
**Action:** Fix in the same session. Mention in close-out under standard findings.

### Category 2: Prior-Session Bug
A bug in a prior session's code discovered during the current session.
**Action:** Do NOT fix in the current session. Note in close-out under "Issues in prior sessions." After the current session's review, run a targeted fix prompt before the next dependent session.

### Category 3: Scope Gap
The spec didn't account for something the implementation needs.
- **Small** (extra field, validation, test case): implement in session, document as scope addition.
- **Substantial** (new file, new API, files outside session scope): do NOT implement. Note as discovered scope gap. Write follow-up prompt after session review.

### Category 4: Feature Idea / Improvement
Not a bug, not required. Do NOT build it. Note in close-out under "Deferred observations." Triaged during doc-sync.

---

## Escalation Triggers

Escalate to a Tier 3 review conversation if:
1. Segmentation output ratio anomaly: < 50% or > 150% of speaker-turn count
2. Claude API cost per transcript exceeds $0.50
3. Segmentation produces semantically incoherent segments on manual review
4. Test pass count drops below 118
5. `insert_event()` backward compatibility broken
6. Schema change requires migration beyond single ALTER TABLE

Escalate to this Work Journal if (during any session):
- A file not in the session's "Modifies" list needs changes
- A file not in the session's "Creates" list is needed
- Test count exceeds estimate by > 50%
- Claude API behaves unexpectedly
- Segmentation output structure doesn't match the expected Segment dataclass

---

## Reserved Numbers

**DEF:** DEF-020 through DEF-023
**DEC:** DEC-020 through DEC-022

(DEC-017, DEC-018, DEC-019 are already assigned from sprint planning.)

Use the next available number from these ranges when assigning new entries. Log every assignment in the running table below. If an item is resolved during the sprint, mark RESOLVED — do not delete.

---

## Running DEF Table

| DEF # | Description | Status | Source |
|-------|-------------|--------|--------|
| | | | |

## Running DEC Table

| DEC # | Description | Source |
|-------|-------------|--------|
| DEC-017 | Multi-participant events: participant="shared" + participants jsonb array | Planning |
| DEC-018 | Thematic segmentation for both batch seeding and live Granola upload | Planning |
| DEC-019 | Combined segmentation + label call (one Claude call per transcript) | Planning |

---

## Sprint Close-Out Instructions

At sprint close (after S3 or final session), produce:

1. A **filled-in doc-sync prompt** that includes:
   - Sprint summary (goal, sessions completed, test delta, review verdicts)
   - All DEF numbers assigned (with status: OPEN / RESOLVED)
   - All DEC numbers tracked
   - Resolved items that should NOT get new DEF entries
   - Outstanding code-level items
   - The doc-update checklist:
     - `docs/project-knowledge.md`
     - `docs/architecture.md`
     - `docs/decision-log.md` + `docs/dec-index.md`
     - `docs/sprint-history.md`
     - `docs/roadmap.md`
     - `CLAUDE.md`

Use the work-journal-closeout template structure from the workflow metarepo.
