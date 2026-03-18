# Architecture

> Technical blueprint. How the system is built.
> Last updated: 2026-03-18

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
│          cluster_id, xs, created_at, source             │
│                                                         │
│  clusters: id, name, myth_text, centroid_embedding,     │
│            event_count, last_updated                    │
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
Single HTML file with inline JavaScript. Canvas-based rendering. Two views (strata, resonance) with animated transition. Slide-out detail panels for events and archetypes. Fetches event data from backend REST API on load and periodically. Claude myth generation proxied through backend.

Key frontend files (v1):
- `static/index.html` — the entire frontend (migrated from sasa_zamani_v3.html)

### Backend — FastAPI Application
Python application handling all server-side logic. Responsibilities: Telegram webhook processing, Granola transcript parsing, embedding generation, cluster assignment, myth generation proxy, event storage and retrieval.

Key backend files (v1):
- `app/main.py` — FastAPI app, route definitions, startup
- `app/embedding.py` — OpenAI embedding calls, similarity math
- `app/clustering.py` — cluster assignment, centroid management, seed cluster definitions
- `app/telegram.py` — Telegram webhook handler, message parsing
- `app/granola.py` — Granola transcript parser (speaker attribution, segment extraction)
- `app/myth.py` — Claude API proxy, prompt construction, caching
- `app/models.py` — Pydantic models for request/response validation
- `app/db.py` — Supabase client, queries

### Database — Supabase
Managed Postgres with pgvector extension. Stores events with their embedding vectors, cluster definitions with centroid embeddings, and cached myth text. Cosine similarity queries for cluster assignment run in SQL.

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | HTML/JS/Canvas | Single file, no build step |
| Backend | Python 3.12 + FastAPI | Async, auto-generated API docs |
| Database | Supabase (Postgres 15 + pgvector) | Managed, free tier |
| Embeddings | OpenAI text-embedding-3-small | 1536 dimensions, via Python SDK |
| Myth generation | Claude claude-sonnet-4-20250514 | Via Anthropic Python SDK |
| Telegram | python-telegram-bot | Webhook mode |
| Deployment | Railway | Auto-deploy from GitHub |
| Version control | Git + GitHub | Two-Claude architecture bridge |
| Production URL | https://web-production-0aa47.up.railway.app | Telegram webhook: /telegram |

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Serve the Sasa Map frontend |
| GET | `/events` | Return all events as JSON. Optional `?participant=` filter |
| GET | `/clusters` | Return cluster definitions with archetype names and centroids |
| POST | `/telegram` | Telegram webhook receiver. Validates, extracts, embeds, stores |
| POST | `/granola` | Upload Granola transcript. Parses, attributes, embeds, stores |
| POST | `/myth` | Generate mythic sentence for a cluster. Caches result |
| GET | `/health` | Health check for Railway |

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
  day INTEGER                      -- days since first event (computed)
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

### Myth Regeneration Trigger
Myth text is regenerated when a cluster's event count has changed by 3+ since the last generation. The old myth is preserved in the myths table (revision history). The frontend requests myth text via `/myth` endpoint; the backend checks cache freshness and regenerates if stale.

### Granola Transcript Parsing
1. Split transcript on speaker label patterns (`Speaker A:`, `Speaker B:`, etc.)
2. User maps speaker labels to participant names at upload time
3. Each speaker turn becomes one event (or multiple if the turn exceeds a length threshold — [To be determined during Sprint 1])
4. Event label: first 5-7 words of the turn, cleaned
5. Event note: full turn text
6. Each event is embedded and clustered independently

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
│   ├── granola.py           # Granola transcript parser
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
│   └── ...                  # [Pending Sprint 1]
├── config/
│   └── runner.yaml          # [Pending Sprint 1]
├── scripts/
│   └── seed_clusters.py     # Initialize seed cluster centroids
├── requirements.txt
├── Procfile                 # Railway deployment
├── CLAUDE.md                # Claude Code session context
└── .env.example             # Required environment variables
```
