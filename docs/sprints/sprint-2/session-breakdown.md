# Sprint 2: Session Breakdown

## Execution Order

```
S1 → S3a → S3b → S2 → S2f → S3c → S3cf → S4 → S4f
```

Backend sessions (S1, S3a, S3b) complete before frontend sessions (S2, S3c, S4) begin. This ensures the frontend always develops against a complete, tested API.

## Dependency Graph

```
S1 (backend xs) ────────────────────────┐
S3a (myth module) → S3b (myth endpoint) ─┤
                                         ▼
                               S2 (frontend data + rendering) → S2f
                                         │
                               S3c (frontend panels) → S3cf
                                         │
                               S4 (participant + polish) → S4f
```

S1 and S3a are parallelizable (no shared files). Grouped sequentially for human-in-the-loop simplicity.

---

## Session S1: Backend xs Computation + API Response Enrichment

**Objective:** Add server-side xs computation to the cluster assignment flow and enrich API responses with fields the frontend needs.

**Creates:**
- `scripts/backfill_xs.py` — one-time script to populate xs for existing events

**Modifies:**
- `app/clustering.py` — add `compute_xs(cluster_name, event_index, cluster_event_count)` function; call it during `assign_cluster` flow
- `app/db.py` — add `xs` and `day` params to `insert_event`; add `update_event_xs` function for backfill
- `app/models.py` — add `xs: float | None` and `day: int | None` to `EventResponse`; add `glyph_id: str | None`, `myth_text: str | None`, `is_seed: bool` to `ClusterResponse`

**Integrates:** Sprint 1 cluster assignment pipeline — hooks into end of assignment flow.

**Parallelizable:** true — no file overlap with S3a.

**Justification for parallelizable:** Creates `scripts/backfill_xs.py` and modifies `clustering.py`, `db.py`, `models.py`. S3a creates `app/myth.py` and modifies `app/config.py`. Zero shared files.

### Compaction Risk Score

| Factor | Detail | Points |
|--------|--------|--------|
| New files created | `scripts/backfill_xs.py` (1) | +2 |
| Files modified | `clustering.py`, `db.py`, `models.py` (3) | +3 |
| Pre-flight reads | `clustering.py`, `db.py`, `models.py`, `config.py` (4) | +4 |
| New tests | ~6 | +3 |
| Complex integration | No (simple addition to pipeline end) | +0 |
| External API | No | +0 |
| Large single file | No | +0 |
| **Total** | | **12** |

**Risk: Medium — proceed with caution.**

### Tests (~6)
- `compute_xs` returns correct range for each seed cluster name
- `compute_xs` applies per-event offset (no identical values for sequential events in same cluster)
- `compute_xs` returns valid float in [0.0, 1.0] for unknown cluster name (fallback)
- `insert_event` stores xs when provided
- `EventResponse` serializes xs and day fields
- `ClusterResponse` serializes glyph_id, myth_text, is_seed fields

---

## Session S3a: Myth Module + Tests

**Objective:** Implement the myth generation module — prompt construction, Claude API call, cache logic, regeneration trigger.

**Creates:**
- `app/myth.py` (~80-100 lines) — complete implementation replacing the 1-line stub

**Modifies:**
- `app/config.py` — add `anthropic_api_key: str` to `Settings`

**Integrates:** Reads from `app/db.py` (cluster data, event labels, myth cache).

**Parallelizable:** true — no file overlap with S1.

**Justification for parallelizable:** Creates `app/myth.py` and modifies `app/config.py`. S1 modifies `clustering.py`, `db.py`, `models.py` and creates `scripts/backfill_xs.py`. Zero shared files.

### Compaction Risk Score

| Factor | Detail | Points |
|--------|--------|--------|
| New files created | `app/myth.py` (1) | +2 |
| Files modified | `app/config.py` (1) | +1 |
| Pre-flight reads | `myth.py`, `db.py`, `config.py`, `models.py` (4) | +4 |
| New tests | ~6 | +3 |
| Complex integration | No | +0 |
| External API | Claude API (mocked in tests, but debugging prompt shape) | +3 |
| Large single file | No | +0 |
| **Total** | | **13** |

**Risk: Medium (upper bound) — proceed with caution.**

### Tests (~6)
- `build_myth_prompt` includes archetype name and event labels
- `build_myth_prompt` includes ancestral register instructions and prohibited words
- `generate_myth` returns parsed text from Claude response (mocked)
- `generate_myth` returns "The pattern holds." on API error (mocked)
- `should_regenerate` returns true when event_count exceeds last generation by 3+
- `should_regenerate` returns false when event_count delta < 3

---

## Session S3b: Myth Endpoint Wiring

**Objective:** Wire the myth module into the FastAPI route. Add request/response models.

**Creates:** —

**Modifies:**
- `app/main.py` — implement `/myth` POST route body (replace stub)
- `app/models.py` — add `MythRequest`, `MythResponse`

**Integrates:** `app/myth.py` → `app/main.py` route handler.

**Parallelizable:** false — depends on S3a.

### Compaction Risk Score

| Factor | Detail | Points |
|--------|--------|--------|
| New files created | — | +0 |
| Files modified | `main.py`, `models.py` (2) | +2 |
| Pre-flight reads | `main.py`, `myth.py`, `models.py`, `db.py` (4) | +4 |
| New tests | ~4 | +2 |
| Complex integration | No | +0 |
| External API | No (myth module already tested) | +0 |
| Large single file | No | +0 |
| **Total** | | **8** |

**Risk: Low.**

### Tests (~4)
- `POST /myth` with valid cluster_id returns myth_text and cached flag
- `POST /myth` with invalid cluster_id returns 404
- `POST /myth` with missing body returns 400
- `POST /myth` cache hit returns without Claude call (mocked, verify no API invocation)

---

## Session S2: Frontend Data Layer + Rendering

**Objective:** Replace all hardcoded data with live API fetches. Adapt both views to render with the new data shape.

**Creates:** —

**Modifies:**
- `static/index.html` — remove hardcoded `EVENTS`, `CLUSTERS`, `TC` arrays; add async data fetch on load; build UUID→archetype mapping; compute `day` from `created_at`; read `xs` from API; construct edge array from cluster co-membership as generic `{source, target, weight}` objects; adapt strata and resonance position calculations; adapt glyph/color lookups from `glyph_id`; adapt edge rendering to consume edge array; add empty state; handle fetch errors

**Integrates:** `/events` (with xs, day), `/clusters` (with glyph_id, myth_text, is_seed) from S1 + S3b.

**Parallelizable:** false — depends on S1 and S3b (needs enriched API responses).

### Compaction Risk Score

| Factor | Detail | Points |
|--------|--------|--------|
| New files created | — | +0 |
| Files modified | `index.html` (1) | +1 |
| Pre-flight reads | `index.html`, `models.py` (2) | +2 |
| New tests | 0 (visual verification) | +0 |
| Complex integration | fetch → data transform → render pipeline | +3 |
| External API | No | +0 |
| Large single file | `index.html` >150 lines | +2 |
| **Total** | | **8** |

**Risk: Low.**

### Visual Verification Checklist
- [ ] Page loads without console errors (real data)
- [ ] Page loads without console errors (empty database)
- [ ] Empty state message displays correctly
- [ ] Strata view: events positioned on time×semantic grid
- [ ] Resonance view: events grouped around archetype centers
- [ ] Animated transition between views functions
- [ ] Cluster name labels visible and correctly positioned
- [ ] Node colors reflect archetype cluster colors
- [ ] Edge lines render between co-cluster events
- [ ] Cluster rings visible in resonance view

---

## Session S2f: Visual Review Fixes

**Contingency, 0.5 session.** Addresses rendering issues discovered during S2 visual verification. If S2 verification passes cleanly, this session is unused.

---

## Session S3c: Frontend Panel Adaptation

**Objective:** Wire event panel, archetype panel, and chained navigation to work with real API data. Connect myth fetching to backend `/myth` endpoint.

**Creates:** —

**Modifies:**
- `static/index.html` — adapt `openEventPanel` (real data fields, UUID-based cluster lookup), `openArchetypePanel` (glyph from `glyph_id`, event list from cluster membership), `fetchMyth` (call `/myth` endpoint instead of direct Anthropic API), neighbor list (cluster co-membership instead of tag similarity), spiral canvas (real events sorted by `created_at`)

**Integrates:** S2 data layer + S3b `/myth` endpoint.

**Parallelizable:** false — depends on S2 and S3b.

### Compaction Risk Score

| Factor | Detail | Points |
|--------|--------|--------|
| New files created | — | +0 |
| Files modified | `index.html` (1) | +1 |
| Pre-flight reads | `index.html`, `models.py` (2) | +2 |
| New tests | 0 (visual verification) | +0 |
| Complex integration | myth endpoint + panel data wiring | +3 |
| External API | No | +0 |
| Large single file | `index.html` | +2 |
| **Total** | | **8** |

**Risk: Low.**

### Visual Verification Checklist
- [ ] Event node click opens panel with correct data
- [ ] Event panel shows label, note, participant, day
- [ ] Event panel shows archetype glyph + name as clickable link
- [ ] Archetype name click opens archetype panel
- [ ] Archetype panel shows glyph (72px), name, event count
- [ ] Myth text loads (shows "reading the pattern…" then resolves)
- [ ] Spiral canvas renders with real events
- [ ] Spiral animation runs and stops on panel close
- [ ] Neighbor events listed (top 3 from same cluster)
- [ ] Neighbor click opens their event panel (chained navigation)
- [ ] Archetype glyph click in event panel opens archetype panel

---

## Session S3cf: Visual Review Fixes

**Contingency, 0.5 session.** Addresses panel/interaction issues discovered during S3c visual verification.

---

## Session S4: Participant Colors + Toggle + Polish

**Objective:** Add participant color encoding to nodes, build individual/collective toggle, final cleanup.

**Creates:** —

**Modifies:**
- `static/index.html` — add participant→color mapping (CSS vars and JS constants), modify node rendering to use participant color, add toggle UI element (DM Mono styled, near view toggle), implement opacity fade logic for non-selected participants, apply fade to edges involving faded events, add empty state handling, remove any remaining mock data references or dead code paths

**Integrates:** All prior sessions.

**Parallelizable:** false — depends on all prior sessions.

### Compaction Risk Score

| Factor | Detail | Points |
|--------|--------|--------|
| New files created | — | +0 |
| Files modified | `index.html` (1) | +1 |
| Pre-flight reads | `index.html`, `design-reference.md` (2) | +2 |
| New tests | 0 (visual verification) | +0 |
| Complex integration | No | +0 |
| External API | No | +0 |
| Large single file | `index.html` | +2 |
| **Total** | | **5** |

**Risk: Low.**

### Visual Verification Checklist
- [ ] Jessie events render in #7F77DD
- [ ] Emma events render in #D85A30
- [ ] Steven events render in #1D9E75
- [ ] Shared events render in #BA7517 (if any exist)
- [ ] Toggle UI visible, styled in DM Mono, positioned near view toggle
- [ ] "All" selected: all events at normal opacity
- [ ] Individual selected: their events full, others ~15%
- [ ] Edges fade proportionally with their connected events
- [ ] Toggle persists across strata ↔ resonance transition
- [ ] No hardcoded mock events anywhere in codebase
- [ ] Event panel shows participant name with color indicator
- [ ] Full end-to-end: send Telegram message → reload page → event appears → click → panel → myth loads

---

## Session S4f: Visual Review Fixes

**Contingency, 0.5 session.** Final polish if needed.

---

## Summary

| Session | Score | Risk | Parallelizable |
|---------|-------|------|----------------|
| S1 | 12 | Medium | true (with S3a) |
| S3a | 13 | Medium | true (with S1) |
| S3b | 8 | Low | false |
| S2 | 8 | Low | false |
| S3c | 8 | Low | false |
| S4 | 5 | Low | false |
| **Max** | **13** | | |

No session at 14+. All clear to proceed.
