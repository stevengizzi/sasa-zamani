# Architecture

> Technical blueprint. How the system is built.
> Last updated: 2026-03-19

## Overview

Sasa/Zamani is a meaning-making tool that takes raw lived experience (Telegram messages, conversation transcripts) and, through AI-assisted semantic clustering and myth generation, helps individuals and communities see what their life is mythologically about. The system has four conceptual layers (Data → Archetype → Truth → Myth); v1 implements Layers 1-2 with partial Layer 4 (mythic sentences per cluster, not full narrative myth).

The architecture is a classic three-tier web application: a canvas-based frontend visualization served as a static file, a Python/FastAPI backend handling all API integrations and data processing, and a Postgres database with vector similarity support.

## System Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    INPUT SOURCES                         │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │ Telegram Bot  │  │ Granola      │  │ Manual Entry  │ │
│  │ (webhook)     │  │ (upload)     │  │ (deferred)    │ │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────┘ │
└─────────┼─────────────────┼──────────────────┼──────────┘
          │                 │                  │
          ▼                 ▼                  ▼
┌─────────────────────────────────────────────────────────┐
│                 FASTAPI BACKEND (Railway)                │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────┐  │
│  │ /telegram    │  │ /granola    │  │ /events (GET)  │  │
│  │ webhook      │  │ upload      │  │ event retrieval│  │
│  └──────┬───────┘  └──────┬──────┘  └────────────────┘  │
│         │                 │                              │
│         ▼                 ▼                              │
│  ┌─────────────────────────────┐  ┌──────────────────┐  │
│  │ EMBEDDING PIPELINE          │  │ /myth            │  │
│  │ OpenAI text-embedding-3-sm  │  │ Claude API proxy │  │
│  │ → vector (1536 dim)         │  │ myth generation  │  │
│  │ → cluster assignment        │  │ + caching        │  │
│  └──────────┬──────────────────┘  └──────────────────┘  │
└─────────────┼────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│              SUPABASE (Postgres + pgvector)              │
│                                                         │
│  events: id, label, note, participant, embedding,       │
│          cluster_id, xs, created_at, event_date, source             │
│                                                         │
│  clusters: id, name, myth_text, centroid,                │
│            event_count, last_updated, is_seed            │
│                                                         │
│  myths: cluster_id, text, generated_at, version         │
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│              FRONTEND (static HTML/JS/Canvas)            │
│                                                         │
│  Sasa Map: strata view + resonance view                 │
│  Animated transition between views                      │
│  Event node click → event detail panel                  │
│  Archetype name click → archetype detail panel          │
│  Chained panel navigation (internal links)              │
│  Individual / collective toggle                         │
│  Participant color encoding                             │
└─────────────────────────────────────────────────────────┘
```

## Components

### Frontend — The Sasa Map
Single HTML file with inline JavaScript. Canvas-based rendering. Two views (strata, resonance) with animated transition. Slide-out detail panels for events and archetypes with chained internal navigation (event→archetype, archetype→event). Fetches live data from `/events` and `/clusters` endpoints on load (migrated from hardcoded mock data in Sprint 2). Claude myth generation proxied through backend via `/myth` endpoint. Participant color encoding (Jessie purple, Emma coral, Steven teal, shared gold) with individual/collective toggle and opacity fade for non-selected participants.

Key frontend files (v1):
- `static/index.html` — the entire frontend (migrated from sasa_zamani_v3.html)

### Backend — FastAPI Application
Python application handling all server-side logic. Responsibilities: Telegram webhook processing, Granola transcript parsing, embedding generation, cluster assignment, myth generation proxy, event storage and retrieval.

Key backend files (v1):
- `app/main.py` — FastAPI app, route definitions, startup
- `app/config.py` — Centralized configuration (env vars, thresholds)
- `app/embedding.py` — OpenAI embedding calls, similarity math
- `app/clustering.py` — cluster assignment, centroid management, seed cluster definitions
- `app/telegram.py` — Telegram webhook handler, raw JSON parsing (DEC-012)
- `app/granola.py` — Granola transcript parser (calls `segment_transcript()` for thematic segmentation, DEC-018)
- `app/segmentation.py` — Thematic segmentation engine: `Segment` dataclass, `segment_transcript()` (boundary-based prompt with line-numbered transcript, single Claude call per transcript, DEC-019/DEC-020), `generate_event_label()` (standalone label generation for Telegram events), `_create_client()` helper with `timeout=120.0`. Model: claude-sonnet-4-20250514
- `app/myth.py` — Claude API proxy, prompt construction, caching (build_myth_prompt, should_regenerate, generate_myth, get_or_generate_myth). PROHIBITED_WORDS list enforces ancestral register.
- `app/models.py` — Pydantic models for request/response validation (includes MythRequest/MythResponse)
- `app/db.py` — Supabase client, queries (includes get_cluster_by_id, get_cluster_events_labels, get_latest_myth, insert_myth, update_cluster_myth). `insert_event()` accepts optional `participants` parameter

### Batch Seeding — seed_transcript.py
CLI tool for batch-seeding events from Granola transcript files. Features: speaker label remapping (e.g., `--map "Speaker A=emma"`), minimum segment length filtering, `--dry-run` mode for preview, and `--date` argument to set `event_date` explicitly for all seeded events. Uses the same embedding/clustering pipeline as the live ingestion paths. Located at `scripts/seed_transcript.py`.

### Database — Supabase
Managed Postgres with pgvector extension. Stores events with their embedding vectors, cluster definitions with centroid embeddings, and cached myth text. Cosine similarity queries for cluster assignment run in SQL.

**Operational note:** `ensure_schema()` at startup verifies that required tables exist (probes) but does not create them. supabase-py cannot execute DDL. Schema creation is a one-time operation via `scripts/init_supabase.sql` in the Supabase SQL editor. The canonical column name in the clusters table is `centroid` (not `centroid_embedding`).

**Postgres RPC function:** `increment_event_count(cid UUID)` atomically increments a cluster's `event_count` by 1. Created manually in the Supabase SQL editor (DEC-015). Called via `client.rpc("increment_event_count", {"cid": cluster_id})` from both the Telegram and Granola pipelines. Replaces the prior read-then-write pattern (DEF-010).

**`event_date` column:** The `events` table includes an `event_date TIMESTAMPTZ` column representing when the event actually occurred (as opposed to `created_at`, which is when it was logged). Batch seeding via `seed_transcript.py` sets `event_date` explicitly from the `--date` CLI argument. The live pipeline (Telegram/Granola) does not set `event_date`; the frontend falls back to `created_at` when `event_date` is null. `EventResponse` in `app/models.py` exposes this field as `event_date: datetime | None = None` (DEC-016).

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | HTML/JS/Canvas | Single file, no build step |
| Backend | Python 3.11.8 (local) / 3.13.12 (Railway) + FastAPI | Async, auto-generated API docs |
| Database | Supabase (Postgres 15 + pgvector) | Managed, free tier |
| Embeddings | OpenAI text-embedding-3-small | 1536 dimensions, via Python SDK |
| Myth generation | Claude claude-sonnet-4-20250514 | Via Anthropic Python SDK |
| Telegram | python-telegram-bot | Webhook mode |
| Deployment | Railway | Auto-deploy from GitHub |
| Version control | Git + GitHub | Two-Claude architecture bridge |
| Production URL | https://web-production-0aa47.up.railway.app | Telegram webhook: /telegram |
| GitHub | https://github.com/stevengizzi/sasa-zamani.git | Source repository |

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Serve the Sasa Map frontend |
| GET | `/events` | Return all events as JSON. Optional `?participant=` filter |
| GET | `/clusters` | Return cluster definitions with archetype names and centroids |
| POST | `/telegram` | Telegram webhook receiver. Validates, extracts, embeds, stores. Always returns HTTP 200 (non-200 causes Telegram retry storms) |
| POST | `/granola` | Upload Granola transcript. Parses, attributes, embeds, stores |
| POST | `/myth` | Generate mythic sentence for a cluster. Caches result |
| GET | `/health` | Health check — returns `{"status": "healthy", "database": "connected/disconnected"}` |

## Database Schema

```sql
-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Events table
CREATE TABLE events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ DEFAULT now(),
  event_date TIMESTAMPTZ,          -- when the event occurred (vs when it was logged)
  label TEXT NOT NULL,              -- short display name (3-5 words)
  note TEXT,                        -- full message text / description
  participant TEXT NOT NULL,         -- jessie | emma | steven
  source TEXT NOT NULL,             -- telegram | granola | manual
  embedding VECTOR(1536),          -- OpenAI text-embedding-3-small
  cluster_id UUID REFERENCES clusters(id),
  xs FLOAT,                        -- 0.0-1.0 semantic x-position (computed)
  day INTEGER,                     -- days since first event (computed)
  participants JSONB DEFAULT '[]'  -- speaker names per segment (DEC-017)
);

-- Clusters table
CREATE TABLE clusters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,               -- archetype name (e.g., "The Gate")
  glyph_id TEXT,                    -- maps to frontend SVG glyph
  centroid VECTOR(1536),           -- mean embedding of member events
  myth_text TEXT,                   -- current mythic sentence
  myth_version INTEGER DEFAULT 0,
  event_count INTEGER DEFAULT 0,
  last_updated TIMESTAMPTZ DEFAULT now(),
  is_seed BOOLEAN DEFAULT false     -- true for initial 6 seed clusters
);

-- Myths history (for revision tracking)
CREATE TABLE myths (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cluster_id UUID REFERENCES clusters(id),
  text TEXT NOT NULL,
  generated_at TIMESTAMPTZ DEFAULT now(),
  event_count_at_generation INTEGER,
  version INTEGER NOT NULL
);

-- Indexes
CREATE INDEX ON events USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);
CREATE INDEX ON events (participant);
CREATE INDEX ON events (cluster_id);
CREATE INDEX ON clusters USING ivfflat (centroid vector_cosine_ops) WITH (lists = 5);
```

## Key Patterns

### Embedding Pipeline
1. Raw text arrives (Telegram message or Granola segment)
2. Text → OpenAI text-embedding-3-small → 1536-dim vector
3. Cosine similarity against all cluster centroids
4. If max similarity >= JOIN_SIM threshold → assign to that cluster, update centroid
5. If max similarity < JOIN_SIM → create new cluster, request Claude archetype name
6. Store event with embedding and cluster_id

### Cluster Centroid Update
When a new event joins a cluster, the centroid is recomputed as the mean of all member event embeddings. This is an incremental update: `new_centroid = (old_centroid * n + new_embedding) / (n + 1)`. The centroid shifts slightly with each new event, which means cluster boundaries are alive — an event that was borderline may eventually migrate if a better cluster forms nearby.

### Event Processing Pipeline (compute_xs + event_count)
When a new event is stored via Telegram or Granola, the pipeline: (1) embeds the text, (2) assigns to a cluster, (3) calls `compute_xs()` to compute the event's semantic x-position within its cluster (0.0–1.0), (4) increments the cluster's `event_count`. Both `telegram.py` and `granola.py` call these functions after event insertion (wired in Sprint 2).

### Myth Regeneration Trigger
Myth text is regenerated when a cluster's event count has changed by 3+ since the last generation (`should_regenerate` in `app/myth.py`). The old myth is preserved in the myths table (revision history). The frontend requests myth text via `/myth` POST endpoint (`MythRequest` → `MythResponse`); the backend checks cache freshness and regenerates if stale.

### Granola Transcript Parsing
1. Transcript text is sent to `segment_transcript()` from `app/segmentation.py` (DEC-018)
2. The transcript is line-numbered (L001, L002, ...) and sent to Claude in a single API call (DEC-019)
3. Claude returns segment boundaries (start_line/end_line) and labels — not verbatim text (DEC-020)
4. Python slices the original transcript using the boundaries to produce segment text
5. Boundary validation: start > end, out of range, overlapping segments are rejected
6. Multi-speaker segments use `participant="shared"` with a `participants` jsonb array listing all contributing speakers (DEC-017)
7. Each segment is embedded and clustered independently

### Telegram Label Generation
When a Telegram message arrives, `process_telegram_update()` calls `generate_event_label()` from `app/segmentation.py` to produce a 3-5 word LLM-generated label before insertion. On failure, falls back to `text[:80]`.

## Deferred Architecture (Layers 3-4)

### Layer 3 — Truth Candidates
When two or more archetypes connect (share events, or produce related mythic themes), the system generates falsifiable propositional claims. Accept/reject/revise mechanic. Internal scaffolding — visible to participants, not published. Not yet designed at the implementation level.

### Layer 4 — Full Myth
Narrative output generated from validated truths and archetypes. Characters, events, a world. Doesn't state its meaning; enacts it. Published output: "Here's a true story that never happened." Not yet designed at the implementation level.

### Zamani View
A third visualization mode: force-directed field showing archetype nodes (not event nodes) with truth threads between related archetypes. Collective toggle shows/hides other participants' contributions. Fully specified in the build spec but not yet built.

## File Structure

```
sasa-zamani/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, routes, startup
│   ├── embedding.py         # OpenAI embedding calls
│   ├── clustering.py        # Cluster assignment, centroids, seeds
│   ├── telegram.py          # Telegram webhook handler
│   ├── granola.py           # Granola transcript parser (thematic segmentation)
│   ├── segmentation.py      # Thematic segmentation engine + label generation
│   ├── myth.py              # Claude API proxy, caching
│   ├── models.py            # Pydantic models
│   └── db.py                # Supabase client
├── static/
│   └── index.html           # Sasa Map frontend
├── docs/
│   ├── project-knowledge.md
│   ├── architecture.md      # This file
│   ├── decision-log.md
│   ├── dec-index.md
│   ├── risk-register.md
│   ├── roadmap.md
│   └── sprint-history.md
├── tests/
│   ├── conftest.py           # Shared fixtures, env var mocking
│   ├── test_health.py        # Health endpoint tests
│   ├── test_db.py            # Database client tests
│   ├── test_endpoints.py     # REST endpoint tests
│   ├── test_embedding.py     # Embedding pipeline tests
│   ├── test_clustering.py    # Clustering logic tests
│   ├── test_telegram.py      # Telegram webhook tests
│   ├── test_granola.py       # Granola parser tests
│   ├── test_myth.py          # Myth generation tests
│   ├── test_seed_transcript.py # Seed transcript pipeline tests
│   ├── test_segmentation.py   # Segmentation engine tests
│   ├── test_backfill_labels.py # Backfill labels script tests
│   └── test_integration.py   # End-to-end integration tests
├── scripts/
│   ├── __init__.py
│   ├── seed_clusters.py      # Initialize seed cluster centroids
│   ├── seed_transcript.py    # Batch-seed events from Granola transcripts
│   ├── backfill_xs.py        # Backfill xs values for existing events
│   ├── centroid_matrix.py    # Compute centroid similarity matrix
│   ├── cluster_sanity.py     # Validate cluster assignment quality
│   ├── backfill_labels.py    # Retroactive LLM label generation for existing events
│   └── test_myth_quality.py  # Manual myth quality evaluation (not collected by pytest)
├── requirements.txt
├── pyproject.toml            # pytest config, marker registration
├── Procfile                  # Railway deployment
├── CLAUDE.md                 # Claude Code session context
└── .env.example              # Required environment variables
```
