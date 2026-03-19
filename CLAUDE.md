# Sasa/Zamani — Claude Code Context

> Dense, actionable context for Claude Code sessions.
> Last updated: 2026-03-19

## Active Sprint

**No active sprint.** Sprint 2 complete. Sprint 3 ready to plan.

## Current State

- **Sprints completed:** 2 (Backend Foundation + Data Pipeline; Frontend Migration)
- **Active sprint:** None
- **Next sprint:** 3 (Integration Testing + Edge City Demo Prep)
- **Tests:** 123 (118–119 pass, 2–3 skip)
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
│   ├── clustering.py        # Cluster assignment, centroids, seeds
│   ├── telegram.py          # Telegram webhook handler
│   ├── granola.py           # Granola transcript parser
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
│   └── test_integration.py  # End-to-end integration tests
├── scripts/
│   ├── __init__.py
│   ├── seed_clusters.py     # Initialize seed cluster centroids
│   ├── backfill_xs.py       # Backfill xs values for existing events
│   ├── centroid_matrix.py   # Compute centroid similarity matrix
│   └── cluster_sanity.py    # Validate cluster assignment quality
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

Three tables: `events` (id, label, note, participant, source, embedding vector(1536), cluster_id, xs, created_at, event_date), `clusters` (id, name, glyph_id, centroid vector(1536), myth_text, event_count, is_seed), `myths` (cluster_id, text, version, generated_at). pgvector extension enabled. See docs/architecture.md for full DDL.

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

## Language Constraints

The Claude myth prompt must use ancestral register. Banned words: journey, growth, explore, reflect, transformation, powerful, detect, discover, reveal, activate, unlock. Test: "Does it speak from the past, or describe from the outside?" The former is correct.

## Participant Colors

Jessie: #7F77DD · Emma: #D85A30 · Steven: #1D9E75 · Shared: #BA7517

## Deferred Items

Google Calendar integration, voice memo + Whisper, dynamic clustering (HDBSCAN), moon nodes, new event arrival animation, mobile layout, truth layer (Layer 3), full myth layer (Layer 4), zamani view. Sprint 1 carry-forwards: DEF-010 (non-atomic increment_event_count), DEF-011 (duplicated SEED_ARCHETYPES), DEF-012 (non-atomic insert+increment), DEF-013 (unbounded dedup set), DEF-014 (cluster_id as cluster_name). Sprint 2 carry-forwards: DEF-016 (seed_clusters.py does not populate glyph_id).
