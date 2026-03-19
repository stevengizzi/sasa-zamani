# Sprint 2: Regression Checklist

## Backend Pipeline Integrity

- [ ] All 90 existing passing tests still pass (run full suite with `-n auto`)
- [ ] `GET /events` returns correct data with all existing fields (id, label, note, participant, cluster_id, created_at, source) — new fields are additive only
- [ ] `GET /events?participant=jessie` filter still works (case-insensitive)
- [ ] `GET /clusters` returns correct data with all existing fields (id, name, event_count) — new fields are additive only
- [ ] `POST /telegram` webhook processes messages and stores events with embeddings and cluster assignment
- [ ] `POST /granola` upload processes transcripts and stores attributed events
- [ ] `GET /health` returns status and database connection info
- [ ] Embedding pipeline: event text → OpenAI embedding → cosine similarity → cluster assignment → Supabase storage (unchanged except xs added at end)
- [ ] Seed cluster initialization at startup: 6 clusters created if not present, skipped if present
- [ ] `ensure_schema()` still validates tables at startup
- [ ] CLUSTER_JOIN_THRESHOLD=0.3 unchanged

## Config Integrity

- [ ] New config field `anthropic_api_key` recognized by Pydantic `Settings` model (no silently ignored keys)
- [ ] Existing config fields (`supabase_url`, `supabase_key`, `openai_api_key`, `telegram_bot_token`, `cluster_join_threshold`) unchanged
- [ ] App starts successfully with all required env vars set
- [ ] App fails fast with clear error if `ANTHROPIC_API_KEY` missing

## Frontend Preservation

- [ ] Frontend served from `/` route via `FileResponse`
- [ ] Canvas-based rendering architecture intact (no framework, no build step)
- [ ] Both views (strata, resonance) render
- [ ] Animated transition between views functions (smooth, ~45 frames)
- [ ] Slide-out panel system: opens from right, 380px width, close button works
- [ ] Chained navigation: event panel → archetype → archetype panel → event in neighbor list
- [ ] Grain overlay visible at ~4% opacity
- [ ] Cormorant Garamond used for archetype names, myth text, display headings
- [ ] DM Mono used for interface labels, metadata, timestamps
- [ ] Color palette: VOID (#0e0c09) background, GOLD (#c49a3a) for significant accents, VIOLET SLATE (#8a8aaa) for liminal accents, RIVER (#8ab0be) for atmospheric elements, BONE (#e4e8e4) for text
- [ ] View toggle at bottom center, DM Mono, gold border
- [ ] Title tag at top left ("SASA — the living present" or similar)

## Deployment Integrity

- [ ] `Procfile` unchanged
- [ ] `requirements.txt` has `anthropic` SDK if not already present (verify)
- [ ] Railway auto-deploy from GitHub not disrupted
- [ ] Production URL responds: https://web-production-0aa47.up.railway.app
- [ ] Telegram webhook endpoint reachable at production URL

## Data Integrity

- [ ] Existing events in database unchanged (no data loss from migration)
- [ ] Existing cluster centroids unchanged
- [ ] `xs` backfill does not modify other event fields
- [ ] Myth cache entries preserve version history in `myths` table

## No Prohibited Modifications

- [ ] `app/telegram.py` not modified
- [ ] `app/granola.py` not modified
- [ ] `app/embedding.py` not modified
- [ ] `scripts/init_supabase.sql` not modified
- [ ] `scripts/seed_clusters.py` not modified
