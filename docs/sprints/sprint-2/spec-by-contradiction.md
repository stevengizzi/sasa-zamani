# Sprint 2: What This Sprint Does NOT Do

## Out of Scope

1. **Zamani view (third visualization mode):** Deferred to Sprint 5. Force-directed archetype-level field with truth threads is not built, not stubbed, not started.
2. **Scroll/zoom/pan:** Deferred to Sprint 5. Canvas remains fixed viewport.
3. **Mobile layout:** Deferred to Sprint 5 / DEF-006. Desktop-only.
4. **Moon nodes (unaffiliated events):** Deferred per DEF-004. Events with null `cluster_id` are hidden, not rendered as orphan nodes.
5. **New event arrival animation:** Deferred per DEF-005. Events appear on next page load, no live push.
6. **Design Brief aesthetic refinement:** Sprint 4 scope. The existing prototype's grain overlay, typography, and palette are preserved as-is, not polished or refined. No new blur effects, no layering refinement, no atmospheric photography.
7. **Embedding-derived xs projection:** Sprint 4 scope. xs uses cluster-center + offset in Sprint 2, not true semantic axis projection from embedding space.
8. **Embedding-based edge similarity:** Sprint 3 scope. No `/edges` endpoint. No pairwise cosine similarity computation. Edges use cluster co-membership only.
9. **Canvas resize handling:** Not implemented. Canvas sized at page load. Window resize may produce incorrect layout — acceptable for MVP.
10. **Loading/skeleton states:** Beyond the initial "The pattern is still forming" empty state and "reading the pattern…" myth loading text, no skeleton screens, loading spinners, or progressive rendering.
11. **Dynamic cluster creation from frontend:** No UI to create, rename, merge, or delete clusters. Cluster management is backend-only (seed clusters + automatic assignment).
12. **Event editing or deletion from frontend:** No CRUD operations on events from the UI. Read-only visualization.
13. **Myth text editing or regeneration from frontend:** No user-triggered myth refresh. Cache staleness checked server-side only.
14. **Periodic data refresh / live polling:** Frontend fetches data once on page load. No WebSocket, no polling interval, no SSE. Refresh = reload page.
15. **DEF-010 through DEF-014 tech debt:** Not addressed this sprint. Non-atomic operations, duplicated constants, unbounded dedup set, granola cluster_name bug — all carry forward.

## Edge Cases to Reject

1. **Events with null cluster_id:** Hide from rendering. Do not show as unassigned nodes. Log to console if encountered.
2. **Clusters with 0 events:** Show cluster ring/label in resonance view but with no nodes. Do not crash on empty cluster arrays. Do not generate myths for empty clusters.
3. **Missing glyph_id on cluster:** Fall back to a default glyph (simple circle) or omit glyph. Do not crash.
4. **Unknown participant name:** Render node with BONE color (#e4e8e4) as fallback. Do not crash.
5. **Myth generation failure (Claude API timeout/error):** Return "The pattern holds." Do not retry automatically. Log the error server-side.
6. **More than 6 clusters:** Layout algorithm must handle N clusters (resonance view angle computation). Do not hardcode 6.
7. **Events with identical xs and day values:** Minor visual overlap acceptable. Do not implement collision detection or jitter in this sprint.
8. **Very long event labels or notes:** Truncate in panel display. Do not allow layout overflow.
9. **Concurrent myth generation requests for same cluster:** Server returns cached result for second request if first completes first. No distributed lock. Minor duplicate generation acceptable.
10. **xs backfill on events that already have xs values:** Overwrite. Backfill is idempotent.

## Scope Boundaries

- **Do NOT modify:** `app/telegram.py`, `app/granola.py`, `app/embedding.py`, `Procfile`, `scripts/init_supabase.sql`, `scripts/seed_clusters.py`, `scripts/centroid_matrix.py`, `scripts/cluster_sanity.py`
- **Do NOT optimize:** Canvas rendering performance beyond maintaining 30fps with <200 events. No WebGL, no offscreen canvas, no spatial indexing for hit detection.
- **Do NOT refactor:** The single-file frontend architecture (DEC-005). No extraction of JS modules, no build step, no component framework. The file will grow — that is acceptable for v1.
- **Do NOT refactor:** Backend module structure. No reorganization of `app/` directory. Myth module goes in `app/myth.py` alongside existing modules.
- **Do NOT add:** WebSocket or SSE for live data push. No real-time features.
- **Do NOT add:** User authentication or session management. Frontend is public.
- **Do NOT add:** API rate limiting on the myth endpoint. Acceptable for three users.
- **Do NOT add:** Frontend build tooling (bundler, minifier, preprocessor).

## Interaction Boundaries

- This sprint does NOT change the behavior of: `/telegram` webhook processing, `/granola` upload processing, embedding generation, cluster assignment logic (except adding xs computation at the end), seed cluster initialization, health check endpoint.
- This sprint does NOT affect: Telegram bot behavior, Granola transcript parsing, database schema (columns `xs` and `day` already exist in events table), Railway deployment configuration (except adding one env var).

## Deferred to Future Sprints

| Item | Target Sprint | DEF Reference |
|------|--------------|---------------|
| Embedding-derived xs projection | Sprint 4 | NEW (assign during sprint) |
| `/edges` endpoint with real similarity | Sprint 3 | NEW (assign during sprint) |
| Moon nodes for unaffiliated events | Sprint 4+ | DEF-004 |
| New event arrival animation | Sprint 4+ | DEF-005 |
| Mobile layout | Sprint 5 | DEF-006 |
| Canvas resize handling | Sprint 4+ | NEW (assign during sprint) |
| Live data polling / WebSocket | Phase 2+ | Not yet registered |
| Non-atomic increment_event_count | Sprint 3+ | DEF-010 |
| SEED_ARCHETYPES duplication | Sprint 3+ | DEF-011 |
| Non-atomic insert + increment | Sprint 3+ | DEF-012 |
| Unbounded Telegram dedup set | Sprint 3+ | DEF-013 |
| Granola cluster_name bug | Sprint 3+ | DEF-014 |
