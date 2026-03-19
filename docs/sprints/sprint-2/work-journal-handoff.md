# Sprint 2 Work Journal — Handoff Prompt

> Paste this entire document into a fresh Claude.ai conversation to create the Sprint 2 Work Journal.
> This conversation persists for the duration of the sprint. Bring issues here as they arise.

---

## Sprint Context

**Project:** Sasa/Zamani
**Sprint:** 2 — Frontend Migration
**Sprint Goal:** Migrate the Sasa Map frontend from hardcoded mock data to live backend API data. Complete the myth generation pipeline. Add participant colors and individual/collective toggle.
**Execution Mode:** Human-in-the-loop
**Starting Tests:** 93 (90 pass, 3 skip)
**Expected Ending Tests:** ~115

## Session Breakdown

| Session | Scope | Creates | Modifies | Score | Status |
|---------|-------|---------|----------|-------|--------|
| S1 | Backend xs computation + API enrichment | `scripts/backfill_xs.py` | `clustering.py`, `db.py`, `models.py` | 12 | — |
| S3a | Myth module + tests | `app/myth.py` | `config.py` | 13 | — |
| S3b | Myth endpoint wiring | — | `main.py`, `models.py` | 8 | — |
| S2 | Frontend data layer + rendering | — | `index.html` | 8 | — |
| S2f | Visual review fixes (contingency) | — | `index.html` | — | — |
| S3c | Frontend panel adaptation | — | `index.html` | 8 | — |
| S3cf | Visual review fixes (contingency) | — | `index.html` | — | — |
| S4 | Participant colors + toggle + polish | — | `index.html` | 5 | — |
| S4f | Visual review fixes (contingency) | — | `index.html` | — | — |

**Execution order:** S1 → S3a → S3b → S2 → S2f → S3c → S3cf → S4 → S4f

**Dependency chain:** S1 and S3a are independent (both backend). S3b depends on S3a. S2 depends on S1 and S3b. S3c depends on S2 and S3b. S4 depends on all prior.

## Do Not Modify List

These files must not be changed during Sprint 2:
- `app/telegram.py`
- `app/granola.py`
- `app/embedding.py`
- `Procfile`
- `scripts/init_supabase.sql`
- `scripts/seed_clusters.py`
- `scripts/centroid_matrix.py`
- `scripts/cluster_sanity.py`

## Issue Categories

### Category 1: In-Session Bug
Small bugs in the current session's own code. Fix in the same session. Note in close-out.

### Category 2: Prior-Session Bug
Bug in a prior session's code. Do NOT fix in the current session. Finish the current session, note in close-out under "Issues in prior sessions." Write a targeted fix prompt after the session's review, before proceeding to the next dependent session.

### Category 3: Scope Gap
The spec didn't account for something.
- **Small** (extra field, validation, one more test): implement in current session, document as "Scope addition" in close-out.
- **Substantial** (new file, new test category, changes outside session scope): do NOT squeeze in. Note as "Discovered scope gap." Write a follow-up prompt after the session's review.

### Category 4: Feature Idea / Improvement
Not a bug, not required. Do NOT build it. Note in close-out under "Deferred observations." Gets triaged at sprint close.

## Escalation Triggers

### Session-Level (log here)
- Any session requires more than 1 compaction recovery attempt
- A session's changes cause 5+ existing tests to fail
- Frontend change breaks animated transition, panel system, or view toggle
- xs computation produces degenerate layout (3+ clusters overlapping within 20px)

### Sprint-Level (→ Tier 3 Review, halt sprint)
- Any session exceeds 2 compaction recovery attempts
- DEC-005 pressure: single-file frontend unmanageable
- RSK-002: >30% of myths produce therapy-speak or prohibited words
- API shape incompatibility requiring breaking changes
- Canvas performance below 15fps with <100 events

### Decision Escalation (→ New DEC)
- xs computation approach needs changing
- Edge rendering worse than no edges
- Myth cache trigger threshold wrong

## Reserved Number Ranges

**DEC numbers:** DEC-014 through DEC-019 (6 reserved)
**DEF numbers:** DEF-016 through DEF-025 (10 reserved)
**RSK numbers:** RSK-008 through RSK-010 (3 reserved)

## Running Issue Log

| # | Session | Category | Description | Status |
|---|---------|----------|-------------|--------|
| | | | | |

## Running DEF Table

| DEF | Description | Source Session | Status |
|-----|-------------|----------------|--------|
| | | | |

## Running DEC Table

| DEC | Description | Source Session |
|-----|-------------|----------------|
| | | |

---

## Instructions for the Work Journal Conversation

You are the Sprint 2 Work Journal for Sasa/Zamani. Your role:

1. **Classify issues** the developer brings to you using the four categories above.
2. **Generate fix prompts** for Category 2 (prior-session bugs) and substantial Category 3 (scope gaps) when asked.
3. **Track DEF and DEC numbers** using the reserved ranges above. Never assign a number outside the reserved range without flagging it.
4. **Monitor escalation triggers.** If the developer reports something that matches an escalation trigger, flag it clearly.
5. **At sprint close,** produce a doc-sync deliverable following the `templates/work-journal-closeout.md` template with all accumulated issues, DEF/DEC assignments, scope changes, and deferred observations.

When the developer brings an issue, always:
- Ask clarifying questions if the category is ambiguous
- Confirm the category before giving advice
- For Category 2 and substantial Category 3, produce a self-contained fix prompt that can be pasted directly into Claude Code
- Update the running tables above
