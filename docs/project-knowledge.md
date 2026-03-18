# Project Knowledge — Sasa/Zamani

> Tier A operational context for Claude.ai and Claude Code.
> Last updated: 2026-03-18

## What Is This Project

Sasa/Zamani is a meaning-making tool grounded in John Mbiti's Bantu philosophy of time. Users log the texture of their days (Telegram messages, conversation transcripts) and the system clusters events by semantic resonance — not chronology — into constellations that generate mythic language. The four-layer model: raw data (sasa) → archetype pattern recognition → falsifiable truth candidates → myth output. V1 implements Layers 1-2 with mythic sentences per cluster.

The core visualization is the Sasa Map: a canvas-based interface with two views (strata: time × semantic spectrum; resonance: cluster-based ring layout) connected by an animated transition. Events are nodes; clusters are constellations with archetype names and Claude-generated mythic sentences in an ancestral register. Both event nodes and archetype names are clickable, opening slide-out detail panels with chained internal navigation.

**Team:** Jessie (design lead, original concept), Emma (branding, copy, thematic guidance), Steven (technical lead, development, philosophical orientation). Three participants for v1.

**Key philosophical commitments:** Semantic resonance over chronology. The pool organized by activation, not time. Decay is the delivery mechanism — specific events compost, the archetype is what remains. Myth enacts meaning without stating it (myth ≠ fable). The tool assists humans in making patterns and is honest that humans are doing the making (not detecting pre-existing cosmic signals). Language: scaffold, propose, candidate, resonate, vessel, compost, constellation, rhyme. Avoid: detect, discover, reveal, activate, synchronicity.

**Design identity:** "Invisible forces made visible — rendered with scientific precision, felt as myth." River-at-night palette. Cormorant Garamond (mythological register) + DM Mono (data precision). Grain overlay. The single test: "Does it feel like the diagram of something that can't quite be diagrammed?"

## Current State

**Tests:** 0
**Sprints completed:** 0
**Active sprint:** None — bootstrapping complete, ready for Sprint 1
**Production URL:** https://web-production-0aa47.up.railway.app
**Database:** https://kngzaasfcbjccivuqbkt.supabase.co
**Next sprint:** 1 (Backend Foundation + Data Pipeline)
**Prototype:** sasa_zamani_v3.html exists with mocked data, two views, panel system, archetype glyphs, Claude API myth generation. Needs migration to real data.

## Architecture

Three-tier: static HTML/JS/Canvas frontend → Python/FastAPI backend (Railway) → Supabase (Postgres + pgvector).

Input sources: Telegram bot webhook + Granola transcript upload. Embedding: OpenAI text-embedding-3-small (1536 dim). Cluster assignment: cosine similarity against cluster centroids, JOIN_SIM threshold TBD. Myth generation: Claude claude-sonnet-4-20250514, server-side proxy with caching.

See docs/architecture.md for full system diagram, database schema, API endpoints, and file structure.

## Tech Stack

Python 3.12 · FastAPI · Supabase (Postgres 15 + pgvector) · OpenAI embeddings · Claude Sonnet for myth generation · python-telegram-bot · Railway deployment · Single-file HTML/JS/Canvas frontend

## Key Active Decisions

| DEC | Title | Summary |
|-----|-------|---------|
| DEC-001 | Python + FastAPI backend | Over Node.js — stronger embedding ecosystem |
| DEC-002 | Supabase + pgvector | Managed Postgres, vector similarity in SQL |
| DEC-003 | OpenAI text-embedding-3-small | 1536 dim, swap path to local models preserved |
| DEC-004 | Railway deployment | Public HTTPS URL, GitHub auto-deploy |
| DEC-005 | Frontend stays HTML/JS canvas | No framework migration for v1 |
| DEC-006 | Telegram bot + Granola upload | V1 input modalities |
| DEC-007 | Individual + 3-person community | Atomic individual, collective overlay |
| DEC-008 | Two-Claude architecture | Claude.ai planning, Claude Code implementation |
| DEC-009 | Both views + transition + chained panels | Full interaction model from prototype preserved |
| DEC-010 | Claude myth generation, ancestral register | [Inferred — confirm] |
| DEC-011 | Seed clusters, dynamic deferred | [Inferred — confirm] |

See docs/decision-log.md for full rationale, alternatives rejected, and cross-references.

## Key Risks

| RSK | Title | Severity |
|-----|-------|----------|
| RSK-001 | Embedding quality insufficient for meaningful clustering | High |
| RSK-002 | Myth generation fable risk (therapy-speak, generic wisdom) | High |
| RSK-003 | No day-2 retention mechanism (habit loop) | High |
| RSK-004 | Frontend rebuild scope creep | Medium |
| RSK-007 | Philosophical coherence under implementation pressure | Medium |

See docs/risk-register.md for full mitigations.

## Participant Colors

Jessie: #7F77DD (purple) · Emma: #D85A30 (coral) · Steven: #1D9E75 (teal) · Shared: #BA7517 (amber gold)

## Seed Archetypes (v1)

The Gate (dream/threshold/migration) · What the Body Keeps (body/water/morning) · The Table (food/connection/social) · The Silence (silence/solitude) · The Root (memory/family/language) · The Hand (writing/fieldwork)

Each has a unique SVG glyph defined in the prototype. Centroids need recomputation from embedding model (currently tag-based).

## Source Documents

| Document | Author | Date | Purpose |
|----------|--------|------|---------|
| Project Bible v2.0 | Emma + Claude | Mar 14 | Philosophical framework, four-layer model, key distinctions |
| Design Brief v1.0 | Jessie + Claude | Mar 17 | Visual identity, color palette, typography, tone, reference points |
| Specs Handoff Doc v3 | Jessie + Claude | Mar 17 | Prototype state, data model, Telegram integration plan, backend architecture |
| sasa_zamani_v3.html | Jessie + Claude | Mar 17 | Working prototype with mocked data |
| Jessie's Claude conversation | Jessie + Claude | Mar 9-13 | Original concept development, 7 prototype iterations |
| Granola transcript | All three | Mar 17 | Conversation recapping project context, philosophical discussions |

## Workflow

This project uses the claude-workflow methodology.
Metarepo: https://github.com/stevengizzi/claude-workflow

**Two-Claude architecture:** Claude.ai (strategic planning, review) + Claude Code (implementation). Git bridges the two. Autonomous Sprint Runner available for automated execution.

## Reference Documents

| Document | Purpose |
|----------|---------|
| docs/project-knowledge.md | This file (Claude context) |
| docs/architecture.md | Technical blueprint, system diagram, schema, endpoints |
| docs/decision-log.md | All DEC entries with full rationale |
| docs/dec-index.md | Quick-reference DEC index |
| docs/sprint-history.md | Sprint history |
| docs/risk-register.md | Risks and mitigations |
| docs/roadmap.md | Strategic vision, sprint queue, deferred items |
| CLAUDE.md | Claude Code session context |
