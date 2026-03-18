# Sasa/Zamani — Claude Code Context

> Dense, actionable context for Claude Code sessions.
> Last updated: 2026-03-18

## Active Sprint

**No active sprint.** Bootstrap complete. Sprint 1 ready to plan.

## Current State

- **Active sprint:** None
- **Next sprint:** 1 (Backend Foundation + Data Pipeline)
- **Tests:** 0
- **Infrastructure:** Railway: web-production-0aa47.up.railway.app | Supabase: kngzaasfcbjccivuqbkt.supabase.co | Telegram bot: configured, webhook pending Sprint 1
- **Prototype:** sasa_zamani_v3.html exists with mocked data — migration target

## What This Is

Meaning-making tool. Users send Telegram messages about their daily experience. System embeds text, clusters by semantic similarity into "constellations," generates mythic archetype names via Claude. Frontend is a canvas visualization (the Sasa Map) with two views. V1: 3 participants (Jessie, Emma, Steven), individual + collective modes.

Philosophical framework: Mbiti's Bantu time (past pools in front of you, organized by resonance not chronology). Campbell's archetypes as clustering scaffold. Myth = compressed meaning that travels, not fable with stated moral.

## Tech Stack

- **Backend:** Python 3.12 + FastAPI
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
├── scripts/
│   └── seed_clusters.py     # Initialize seed cluster centroids
├── requirements.txt
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

## Language Constraints

The Claude myth prompt must use ancestral register. Banned words: journey, growth, explore, reflect, transformation, powerful, detect, discover, reveal, activate, unlock. Test: "Does it speak from the past, or describe from the outside?" The former is correct.

## Participant Colors

Jessie: #7F77DD · Emma: #D85A30 · Steven: #1D9E75 · Shared: #BA7517

## Deferred Items

Google Calendar integration, voice memo + Whisper, dynamic clustering (HDBSCAN), moon nodes, new event arrival animation, mobile layout, truth layer (Layer 3), full myth layer (Layer 4), zamani view.
