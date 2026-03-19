# Sprint 3 Design Summary

**Sprint Goal:** Populate the Sasa Map with real data from two Granola transcripts, clear the accumulated backend deferred-item backlog (6 items), tune myth generation quality, and polish the frontend for the Edge City demo (~Mar 22).

**Session Breakdown:**
- Session S1a: DB & clustering fixes (DEF-016, DEF-010, DEF-011, xs overlap)
  - Creates: —
  - Modifies: `app/db.py`, `app/clustering.py`, `scripts/seed_clusters.py`
  - Integrates: N/A
- Session S1b: Pipeline fixes (DEF-012, DEF-013, DEF-014)
  - Creates: —
  - Modifies: `app/telegram.py`, `app/granola.py`, `app/db.py`
  - Integrates: N/A
- Session S2: Granola transcript seeding (FF-004)
  - Creates: `scripts/seed_transcript.py`, `tests/test_seed_transcript.py`
  - Modifies: —
  - Integrates: Existing pipeline functions (`embed_text`, `assign_cluster`, `insert_event`, etc.)
- Session S3: Myth prompt refinement
  - Creates: `scripts/test_myth_quality.py`
  - Modifies: `app/myth.py`
  - Integrates: N/A
- Session S4: Frontend demo polish (Esc close, reverse chaining, fade animation, loading state)
  - Creates: —
  - Modifies: `static/index.html`
  - Integrates: N/A
- Session S4f: Visual-review fixes — contingency, 0.5 session
- Session S5: Integration verification + demo walkthrough
  - Creates: `docs/sprints/sprint-3/demo-verification.md`
  - Modifies: —
  - Integrates: All prior sessions

**Key Decisions:**
- Gate xs center → 0.08, Silence xs center → 0.20 (was 0.12/0.15; Jessie reviews after)
- Minimum transcript segment length: 100 chars (filters noise like "Yeah." / "Oh.")
- March 17 speakers: A→steven, B→emma, C→jessie
- March 18 speakers: B→emma, C→jessie, F→steven, all others→shared
- Myth prompt refined using Design Brief + Project Bible as quality gate (Emma reviews post-sprint)
- Telegram webhook confirmed working — no debugging session needed

**Scope Boundaries:**
- IN: Backend deferred cleanup (DEF-010/011/012/013/014/016), transcript seeding (FF-004), myth prompt refinement, frontend polish (Esc/reverse chain/fade/loading), integration verification
- OUT: Design Brief visuals (Sprint 4), FF-002 thematic segmentation, new input modalities, mobile, dynamic clustering, moon nodes, truth candidates, Layer 3/4

**Regression Invariants:**
- All existing tests pass (≥122 pass, ≤3 skip)
- All API endpoint response contracts unchanged
- Telegram and Granola pipeline happy paths unbroken
- Frontend: both views, transition, panels, toggle all functional
- Myth caching logic unchanged (prompt text change only)

**File Scope:**
- Modify: `app/db.py`, `app/clustering.py`, `app/telegram.py`, `app/granola.py`, `app/myth.py`, `scripts/seed_clusters.py`, `static/index.html`
- Create: `scripts/seed_transcript.py`, `tests/test_seed_transcript.py`, `scripts/test_myth_quality.py`
- Do not modify: `app/config.py`, `app/models.py`, `app/embedding.py`, `app/main.py`, `scripts/init_supabase.sql`, `tests/conftest.py`

**Config Changes:** No config changes.

**Test Strategy:**
- ~21 new tests (7 + 5 + 6 + 3 + 0)
- Baseline ~125 → target ~146
- Full suite run at each session close: `pytest -n auto`

**Runner Compatibility:**
- Mode: Human-in-the-loop
- Parallelizable sessions: none
- No runner config generated

**Dependencies:**
- Sprint 2 complete, Telegram webhook working, production Supabase accessible
- OpenAI API for ~400 embeddings, Anthropic API for myth testing
- Both transcripts in repo

**Escalation Criteria:**
- Atomic increment requires schema change → Tier 3
- Seeding produces >500 events → pause and assess
- Myth output fails tonal test after 3+ iterations → escalate
- Frontend changes break existing interactions → stop
- Test pass count drops below 118 → investigate

**Doc Updates Needed:**
- project-knowledge.md, sprint-history.md, architecture.md, decision-log.md, dec-index.md, risk-register.md, roadmap.md, CLAUDE.md
