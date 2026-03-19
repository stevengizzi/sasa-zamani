# Sasa/Zamani — Claude Code Context

> Dense, actionable context for Claude Code sessions.
> Last updated: 2026-03-20

## Active Sprint

**No active sprint.** Sprint 4 complete. Sprint 5 ready to plan.

## Current State

- **Sprints completed:** 4 (Backend Foundation + Data Pipeline; Frontend Migration; Integration Testing + Edge City Demo Prep; Thematic Segmentation + LLM Labels; Data Quality + Significance Filtering)
- **Active sprint:** None
- **Next sprint:** 5 (Design Brief Alignment)
- **Tests:** 237 (237 pass, 0 skip)
- **Infrastructure:** Railway: web-production-0aa47.up.railway.app | Supabase: kngzaasfcbjccivuqbkt.supabase.co | Telegram bot: webhook active at /telegram
- **GitHub:** https://github.com/stevengizzi/sasa-zamani.git

## What This Is

Meaning-making tool. Users send Telegram messages about their daily experience. System embeds text, clusters by semantic similarity into "constellations," generates mythic archetype names via Claude. Frontend is a canvas visualization (the Sasa Map) with two views. V1: 3 participants (Jessie, Emma, Steven), individual + collective modes.

Philosophical framework: Mbiti's Bantu time (past pools in front of you, organized by resonance not chronology). Campbell's archetypes as clustering scaffold. Myth = compressed meaning that travels, not fable with stated moral.

## Tech Stack

- **Backend:** Python 3.11.8 (local) / 3.13.12 (Railway) + FastAPI
- **Database:** Supabase (Postgres 15 + pgvector)
- **Embeddings:** OpenAI text-embedding-3-small (1536 dim)
- **Myth generation:** Claude claude-sonnet-4-20250514 via Anthropic SDK
- **Telegram:** python-telegram-bot (webhook mode)
- **Frontend:** Single HTML/JS/Canvas file (served as static)
- **Deployment:** Railway (auto-deploy from GitHub)

## Project Structure

```
sasa-zamani/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, routes, startup
│   ├── config.py            # Centralized configuration
│   ├── embedding.py         # OpenAI embedding calls
│   ├── clustering.py        # Cluster assignment, centroids, seeds, dynamic creation
│   ├── telegram.py          # Telegram webhook handler
│   ├── granola.py           # Granola transcript parser (thematic segmentation)
│   ├── segmentation.py      # Thematic segmentation engine + label generation + significance
│   ├── archetype_naming.py  # Deferred archetype naming for dynamic clusters
│   ├── myth.py              # Claude API proxy, caching
│   ├── models.py            # Pydantic models
│   └── db.py                # Supabase client
├── static/
│   └── index.html           # Sasa Map frontend
├── docs/                    # Canon documents
├── tests/
│   ├── conftest.py          # Shared fixtures, env var mocking
│   ├── test_health.py       # Health endpoint tests
│   ├── test_db.py           # Database client tests
│   ├── test_endpoints.py    # REST endpoint tests
│   ├── test_embedding.py    # Embedding pipeline tests
│   ├── test_clustering.py   # Clustering logic tests
│   ├── test_telegram.py     # Telegram webhook tests
│   ├── test_granola.py      # Granola parser tests
│   ├── test_myth.py         # Myth generation tests
│   ├── test_seed_transcript.py # Seed transcript pipeline tests
│   ├── test_segmentation.py # Segmentation engine tests
│   ├── test_archetype_naming.py # Archetype naming tests
│   ├── test_backfill_labels.py # Backfill labels script tests
│   └── test_integration.py  # End-to-end integration tests
├── scripts/
│   ├── __init__.py
│   ├── seed_clusters.py     # Initialize seed cluster centroids
│   ├── seed_transcript.py   # Batch-seed events from Granola transcripts
│   ├── backfill_xs.py       # Backfill xs values for existing events
│   ├── centroid_matrix.py   # Compute centroid similarity matrix
│   ├── cluster_sanity.py    # Validate cluster assignment quality
│   ├── backfill_labels.py   # Retroactive LLM label generation for existing events
│   ├── test_myth_quality.py # Manual myth quality evaluation (not collected by pytest)
│   ├── migrate_sprint4.sql  # Sprint 4 schema migration
│   └── init_supabase.sql    # Full schema DDL
├── requirements.txt
├── pyproject.toml           # pytest config, marker registration
├── Procfile                 # Railway: web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
├── CLAUDE.md                # This file
└── .env.example
```

## Environment Variables

```
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
TELEGRAM_BOT_TOKEN=
SUPABASE_URL=
SUPABASE_KEY=
CLUSTER_JOIN_THRESHOLD=0.3
SIGNIFICANCE_THRESHOLD=0.3
ARCHETYPE_NAMING_THRESHOLD=3
```

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Serve frontend |
| GET | `/events` | All events (optional `?participant=` filter) |
| GET | `/clusters` | Cluster definitions + archetype names |
| POST | `/telegram` | Telegram webhook |
| POST | `/granola` | Upload Granola transcript |
| POST | `/myth` | Claude myth generation (cached) |
| GET | `/health` | Health check |

## Database Schema (Supabase)

Four tables: `events` (id, label, note, participant, source, embedding vector(1536), cluster_id, xs, created_at, event_date, participants jsonb, raw_input_id FK, start_line, end_line), `clusters` (id, name, glyph_id, centroid vector(1536), myth_text, event_count, is_seed), `myths` (cluster_id, text, version, generated_at), `raw_inputs` (id, text, source, source_metadata jsonb, created_at). pgvector extension enabled. See docs/architecture.md for full DDL.

## Key Decisions

- DEC-001: Python + FastAPI (not Node)
- DEC-002: Supabase + pgvector (not standalone vector DB)
- DEC-003: OpenAI text-embedding-3-small (swap path to local preserved)
- DEC-005: Frontend stays as single HTML file (no React migration)
- DEC-009: Both strata + resonance views, animated transition, chained panel navigation
- DEC-011: Seed clusters (6 archetypes), dynamic clustering deferred
- DEC-012: Raw JSON webhook over python-telegram-bot
- DEC-013: In-memory dedup for Telegram updates
- DEC-014: Lifted do-not-modify constraint on telegram.py/granola.py for pipeline wiring
- DEC-015: Atomic increment via Postgres RPC (resolves DEF-010)
- DEC-016: Lifted do-not-modify on app/models.py for event_date field
- DEC-017: Multi-participant events: participant="shared" + participants jsonb array
- DEC-018: Thematic segmentation for batch and live Granola pipelines
- DEC-019: Combined segmentation + label in single Claude call
- DEC-020: Boundary-based segmentation output (line numbers, not text)
- DEC-021: Significance filtering in both pipelines (threshold 0.3)
- DEC-022: raw_inputs table for all incoming data
- DEC-023: Deferred archetype naming ("The Unnamed" until threshold)
- DEC-024: Post-processing label dedup with ordinal suffixes

## Language Constraints

The Claude myth prompt must use ancestral register. Banned words: journey, growth, explore, reflect, transformation, powerful, detect, discover, reveal, activate, unlock. Test: "Does it speak from the past, or describe from the outside?" The former is correct.

## Participant Colors

Jessie: #7F77DD · Emma: #D85A30 · Steven: #1D9E75 · Shared: #BA7517

## Deferred Items

Google Calendar integration, voice memo + Whisper, dynamic clustering (HDBSCAN), moon nodes, new event arrival animation, mobile layout, truth layer (Layer 3), full myth layer (Layer 4), zamani view. Sprint 3 carry-forwards: DEF-017 (myth post-validation), DEF-018 (transcript dedup). Sprint 3.5 carry-forwards: DEF-020 (per-participant attribution for multi-speaker events). Sprint 4 carry-forwards: DEF-022 (single-event cluster node unclickable in frontend — The Root), DEF-023 (strata view bottom margin overlaps navigation toggles), seed archetype expansion for discussion content, backfill_labels.py tuple return update needed.
