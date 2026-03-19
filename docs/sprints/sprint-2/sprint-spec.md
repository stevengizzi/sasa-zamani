# Sprint 2: Frontend Migration

## Goal

Migrate the Sasa Map frontend from hardcoded mock data to live backend API data, preserving the full interaction model (both views, animated transition, panels, chained navigation). Complete the myth generation pipeline with a server-side Claude endpoint. Add participant color encoding and individual/collective toggle.

## Scope

### Deliverables

1. **Backend xs computation:** Server-side computation of the semantic x-position (`xs`) for each event during cluster assignment, stored in the events table. Backfill script for existing events.
2. **API response enrichment:** `EventResponse` includes `xs`, `day`; `ClusterResponse` includes `glyph_id`, `myth_text`, `is_seed`.
3. **Myth generation module:** Complete `app/myth.py` — prompt construction in ancestral register, Claude API call, cache against `myths` table, regeneration trigger when event_count changes by 3+.
4. **Myth endpoint:** `/myth` POST endpoint accepts a `cluster_id`, returns cached or freshly generated mythic sentence.
5. **Frontend data layer:** `static/index.html` fetches from `/events` and `/clusters` instead of hardcoded arrays. UUID→archetype mapping. Edge array from cluster co-membership.
6. **Frontend rendering adaptation:** Both strata and resonance views render correctly with live data. Animated transition preserved. Glyph and color lookups by `glyph_id`. Empty state handling.
7. **Frontend panel adaptation:** Event panel, archetype panel, and chained navigation work with real data. Myth text fetched from `/myth` endpoint. Spiral canvas with real event data.
8. **Participant color encoding:** Event nodes colored by participant (Jessie #7F77DD, Emma #D85A30, Steven #1D9E75, shared #BA7517).
9. **Individual/collective toggle:** UI toggle filters events by participant with opacity fade. "All" at full opacity; selected participant at full opacity, others at ~15%.
10. **Zero mock data:** No hardcoded event arrays remain in the frontend.

### Acceptance Criteria

1. **Backend xs computation:**
   - `compute_xs(cluster_name)` returns a float in [0.0, 1.0] using cluster canonical positions
   - Per-event offset applied so events within a cluster do not stack at identical xs values
   - `insert_event` stores computed xs in the database
   - `backfill_xs.py` updates all existing events with null xs
   - Cluster xs centers: The Gate ~0.12, The Silence ~0.15, The Hand ~0.25, The Root ~0.38, What the Body Keeps ~0.50, The Table ~0.82

2. **API response enrichment:**
   - `GET /events` response includes `xs` (float or null), `day` (int or null) for each event
   - `GET /clusters` response includes `glyph_id` (string or null), `myth_text` (string or null), `is_seed` (bool)
   - Existing response fields unchanged (additive only)

3. **Myth generation module:**
   - Prompt includes archetype name and event labels from the cluster
   - Prompt specifies ancestral register: "not explanation, not analysis. Short, poetic, oracular."
   - Prompt prohibits words from the design reference "never use" list
   - Claude response parsed to extract single sentence (20-35 words)
   - Result cached in `myths` table with version tracking
   - Regeneration triggered when cluster `event_count` exceeds count at last generation by 3+
   - Graceful failure: returns "The pattern holds." on API error

4. **Myth endpoint:**
   - `POST /myth` with `{"cluster_id": "<uuid>"}` returns `{"myth_text": "...", "cached": true/false}`
   - Cache hit returns immediately without Claude API call
   - Cache miss generates, stores, and returns new myth
   - Invalid cluster_id returns 404
   - Missing/malformed body returns 400

5. **Frontend data layer:**
   - Page load fetches `/events` and `/clusters` before rendering
   - Events mapped to cluster objects by `cluster_id` UUID
   - `xs` read from API response (not computed client-side)
   - `day` computed from `created_at` relative to earliest event (integer days since first event)
   - Edge array constructed from cluster co-membership with weight = 1/(cluster event count)
   - Edge array is a generic `{source, target, weight}` structure (Sprint 3 data swap ready)
   - Fetch failure shows error state, does not crash

6. **Frontend rendering adaptation:**
   - Strata view: events positioned by `day` (y-axis) and `xs` (x-axis)
   - Resonance view: events clustered around archetype centers, layout handles N clusters
   - Animated transition between views functions correctly
   - Cluster colors assigned by archetype identity via `glyph_id` (The Gate/The Table → GOLD, The Silence/The Root → VIOLET SLATE, What the Body Keeps/The Hand → RIVER)
   - Glyphs rendered by `glyph_id` mapping to SVG functions
   - Empty database: centered message "The pattern is still forming" in Cormorant Garamond italic
   - Single-event database: renders without error in both views

7. **Frontend panel adaptation:**
   - Event node click opens panel with: label, note, participant name, day, archetype link with glyph
   - Archetype name click opens panel with: name, glyph (72px), myth text, event count, spiral canvas
   - Myth text loaded from `/myth` endpoint, shows "reading the pattern…" while loading
   - Chained navigation: event panel → archetype glyph/name → archetype panel works
   - Neighbor events: top 3 by cluster co-membership, each clickable → opens their event panel
   - Panel close stops spiral animation, clears panel content
   - Spiral canvas renders with real event data (sorted by created_at)

8. **Participant color encoding:**
   - Node fill color determined by event `participant` field
   - Colors match design reference: jessie=#7F77DD, emma=#D85A30, steven=#1D9E75, shared=#BA7517
   - Panel displays participant name with their color indicator
   - Edge colors unchanged (still determined by cluster archetype color)

9. **Individual/collective toggle:**
   - Toggle UI positioned near the view toggle (bottom of screen), styled with DM Mono
   - Options: "all", "jessie", "emma", "steven"
   - "All" selected: all events at normal opacity
   - Participant selected: their events at full opacity, all other events at ~15% opacity
   - Edges involving faded events also fade proportionally
   - Toggle state persists across view transitions (strata ↔ resonance)
   - Labels and cluster names unaffected by toggle (always visible)

10. **Zero mock data:**
    - No hardcoded `EVENTS` array in `index.html`
    - No hardcoded `CLUSTERS` array with mock positions
    - No hardcoded `TC` tag→cluster mapping
    - No direct calls to `api.anthropic.com` from frontend
    - All data sourced from backend API

### Performance Benchmarks

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| Initial page load (data fetch) | < 2s with < 500 events | Manual timing in browser network tab |
| Myth generation (cache miss) | < 5s | Manual timing, first archetype panel open |
| Myth generation (cache hit) | < 500ms | Manual timing, subsequent panel open |
| Canvas frame rate | 30+ fps with < 200 events | Browser dev tools performance monitor |

### Config Changes

| Env Var | Pydantic Model | Field Name | Type | Default |
|---------|---------------|------------|------|---------|
| `ANTHROPIC_API_KEY` | `Settings` | `anthropic_api_key` | `str` | (required, no default) |

## Dependencies

- Sprint 1 complete: backend deployed, database schema created, seed clusters initialized
- `ANTHROPIC_API_KEY` environment variable set in Railway deployment
- Supabase database accessible with existing seed clusters (6 seed clusters with centroids)
- At least a few test events in the database for visual verification (can send via Telegram bot before frontend sessions)
- `anthropic` Python SDK in `requirements.txt` (verify — may need to add)

## Relevant Decisions

- DEC-005: Frontend stays HTML/JS canvas — no framework migration for v1. All frontend work modifies `static/index.html`.
- DEC-009: Both views + transition + chained panels — full interaction model from prototype preserved.
- DEC-010: Claude myth generation, ancestral register — confirmed Sprint 1, implemented Sprint 2.
- DEC-011: Seed clusters, dynamic deferred — 6 seed clusters active, dynamic clustering deferred.
- NEW DEC (to be assigned): xs computed server-side during cluster assignment, stored in events table. Sprint 2 uses cluster-center + offset; Sprint 4 upgrades to embedding-derived projection.
- NEW DEC (to be assigned): Edges use cluster co-membership in Sprint 2; Sprint 3 adds `/edges` endpoint with real embedding similarity.
- NEW DEC (to be assigned): Frontend edge array consumes generic `{source, target, weight}` structure for forward-compatible data swap.

## Relevant Risks

- RSK-002 (High): Myth generation fable risk — therapy-speak, generic wisdom. Mitigated by explicit prompt constraints (ancestral register, prohibited words, 20-35 word limit). Escalate if >30% of generated myths fail Emma's tonal test.
- RSK-004 (Medium): Frontend rebuild scope creep. Mitigated by strict Specification by Contradiction. This sprint migrates data, not design.
- RSK-007 (Medium): Philosophical coherence under implementation pressure. Myth prompt must hold the line on register. Copy tone for empty states, error states, and labels must follow design reference.

## Session Count Estimate

6 real sessions + 3 contingency visual-review fix slots = 9 worst-case. Backend sessions (S1, S3a, S3b) are straightforward; frontend sessions (S2, S3c, S4) carry visual verification requirements, hence the fix budget. Estimated test delta: +22 (93 → ~115).
