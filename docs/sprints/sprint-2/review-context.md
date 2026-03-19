# Sprint 2: Review Context

> This file is read by all Tier 2 review sessions. It contains the shared context
> that every reviewer needs. Session-specific review prompts reference this file
> by path and add session-specific focus items.

---

## Sprint Spec

### Goal
Migrate the Sasa Map frontend from hardcoded mock data to live backend API data, preserving the full interaction model (both views, animated transition, panels, chained navigation). Complete the myth generation pipeline with a server-side Claude endpoint. Add participant color encoding and individual/collective toggle.

### Deliverables
1. Backend xs computation: server-side computation of semantic x-position during cluster assignment, stored in events table
2. API response enrichment: EventResponse includes xs, day; ClusterResponse includes glyph_id, myth_text, is_seed
3. Myth generation module: complete app/myth.py — prompt construction, Claude API call, cache, regeneration trigger
4. Myth endpoint: /myth POST accepts cluster_id, returns cached or fresh mythic sentence
5. Frontend data layer: index.html fetches from /events and /clusters, builds UUID→archetype mapping, constructs edge array
6. Frontend rendering: both views render with live data, transition preserved, glyph/color lookups by glyph_id, empty state
7. Frontend panels: event and archetype panels with real data, myth from /myth endpoint, chained navigation
8. Participant color encoding: nodes colored by participant per design reference
9. Individual/collective toggle: opacity-fade filter by participant
10. Zero mock data: no hardcoded events, clusters, or tag mappings remain

### Key Decisions
- xs computed server-side (cluster-center + offset for Sprint 2; embedding-derived in Sprint 4)
- Edges use cluster co-membership (embedding similarity deferred to Sprint 3 /edges endpoint)
- Frontend edge array consumes generic {source, target, weight} for forward-compatible swap
- Myth generation via backend /myth endpoint (not direct Anthropic API from browser)
- Toggle: filter with opacity fade (selected participant full opacity, others ~15%)
- Empty state: "The pattern is still forming" in Cormorant Garamond italic

### Config Changes
| Env Var | Pydantic Field | Type |
|---------|---------------|------|
| ANTHROPIC_API_KEY | anthropic_api_key | str (required) |

---

## Specification by Contradiction (Summary)

### Out of Scope
- Zamani view, scroll/zoom/pan, mobile layout, moon nodes, event arrival animation
- Design Brief aesthetic refinement (Sprint 4)
- Embedding-derived xs (Sprint 4), embedding-based edges (Sprint 3)
- Canvas resize handling, loading/skeleton states, dynamic cluster creation
- Event editing/deletion, myth editing, live polling/WebSocket
- DEF-010 through DEF-014 tech debt

### Do NOT Modify
- app/telegram.py, app/granola.py, app/embedding.py
- Procfile, scripts/init_supabase.sql, scripts/seed_clusters.py

### Edge Cases
- Events with null cluster_id: hide, log to console
- Clusters with 0 events: show ring/label, no nodes, no myth
- Missing glyph_id: fallback glyph or omit
- Unknown participant: BONE color fallback
- Myth failure: return "The pattern holds."
- >6 clusters: layout must handle N clusters

---

## Sprint-Level Regression Checklist

### Backend Pipeline Integrity
- [ ] All 90 existing passing tests still pass
- [ ] GET /events returns correct data with all existing fields (additive only)
- [ ] GET /events?participant= filter still works
- [ ] GET /clusters returns correct data with all existing fields (additive only)
- [ ] POST /telegram processes and stores events
- [ ] POST /granola processes and stores events
- [ ] GET /health returns status
- [ ] Embedding pipeline unchanged (except xs at end)
- [ ] Seed cluster initialization at startup unchanged
- [ ] ensure_schema() validates tables at startup
- [ ] CLUSTER_JOIN_THRESHOLD=0.3 unchanged

### Config Integrity
- [ ] New anthropic_api_key recognized by Pydantic Settings
- [ ] Existing config fields unchanged
- [ ] App starts with all required env vars
- [ ] App fails fast if ANTHROPIC_API_KEY missing

### Frontend Preservation
- [ ] Frontend served from / route
- [ ] Canvas-based rendering intact
- [ ] Both views render
- [ ] Animated transition functions
- [ ] Slide-out panel system works
- [ ] Chained navigation works
- [ ] Grain overlay visible
- [ ] Cormorant Garamond + DM Mono typography
- [ ] River-at-night color palette preserved
- [ ] View toggle at bottom center

### Deployment Integrity
- [ ] Procfile unchanged
- [ ] requirements.txt has anthropic SDK
- [ ] Railway auto-deploy not disrupted
- [ ] Production URL responds

### No Prohibited Modifications
- [ ] app/telegram.py not modified
- [ ] app/granola.py not modified
- [ ] app/embedding.py not modified
- [ ] scripts/init_supabase.sql not modified
- [ ] scripts/seed_clusters.py not modified

---

## Sprint-Level Escalation Criteria

### Session-Level (→ Work Journal)
1. Any session requires more than 1 compaction recovery attempt
2. A session's changes cause 5+ existing tests to fail
3. Frontend change breaks animated transition, panel system, or view toggle
4. xs computation produces degenerate layout (3+ clusters overlapping within 20px)

### Sprint-Level (→ Tier 3 Review)
5. Any session exceeds 2 compaction recovery attempts
6. DEC-005 pressure: single-file frontend unmanageable
7. RSK-002: >30% of myths produce therapy-speak or prohibited words
8. API shape incompatibility requiring breaking changes
9. Canvas performance below 15fps with <100 events

### Decision Escalation (→ New DEC)
10. xs approach change needed
11. Edge rendering worse than no edges
12. Myth cache trigger threshold wrong
