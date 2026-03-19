# Roadmap

> Strategic vision and sprint queue.
> Last updated: 2026-03-19

## Vision

A deployed tool where three people (Jessie, Emma, Steven) send Telegram messages and upload conversation transcripts, and watch their lived experience cluster into constellations organized by semantic resonance, each generating mythic language in an ancestral register. The Sasa Map makes visible what their lives are mythologically about — individually and collectively.

Long-term: a meaning-making practice that replaces journaling not by being a better journal, but by being a fundamentally different thing. A journal captures. This mythologizes. The tool extends to communities (popup villages, residencies, gatherings) and eventually to any individual who wants to see the shape of their life's recurring archetypes.

## Phases

### Phase 1 — MVP (Target: this week, ~Mar 22)
A working deployed app that the team can use at the local Edge City gathering. Three participants, Telegram input + Granola upload, real embeddings, constellation formation, mythic sentence generation. Both views (strata, resonance) with the existing interaction model.

**Success criteria:** All three team members have sent 10+ events via Telegram, uploaded at least one Granola transcript, and the Sasa Map shows meaningful constellations with mythic sentences that pass Emma's tonal test.

### Phase 2 — Refinement (Post-MVP, ~2-4 weeks)
Visual polish aligned with the Design Brief. Cormorant Garamond / DM Mono typography. River-at-night palette. Grain overlay. Archetype glyph refinement. Scroll/zoom/pan. Mobile layout. The zamani view (archetype-level force-directed field). Prompt engineering for myth quality.

### Phase 3 — Truth & Myth Layers
Layer 3 (truth candidates) and Layer 4 (full myth output). The accept/reject/revise mechanic. The "publication frame" output: "Here's a true story that never happened." This is where the tool transcends visualization and becomes a meaning-making practice.

### Phase 4 — Community Scaling
Privacy controls (private flag: AI-readable, participant-hidden). Participant management beyond three people. Onboarding flow for new users. The communal problem at scale: what changes with 30 contributors vs. 3?

## Build Track Queue

### Sprint 1 — Backend Foundation + Data Pipeline ✓
**Status:** Complete (9 sessions, tests 0 → 93)

**Delivered:**
- FastAPI app deployed on Railway with health check
- Supabase schema created with pgvector (events, clusters, myths)
- Telegram webhook receiving messages via raw JSON (DEC-012) with in-memory dedup (DEC-013)
- Granola upload endpoint parsing transcripts into attributed events
- Seed cluster centroids computed and validated (6/6 sanity, centroid matrix healthy)
- /events, /clusters, /myth endpoints operational
- CLUSTER_JOIN_THRESHOLD=0.3 calibrated
- RSK-001 downgraded High → Low

### Sprint 2 — Frontend Migration ✓
**Status:** Complete (9 sessions, tests 93 → 123)

**Delivered:**
- Frontend migrated from hardcoded data to async API fetches (`/events`, `/clusters`)
- Strata and resonance views working with real data, animated transition preserved
- Event and archetype detail panels with chained navigation (stopPropagation fix)
- Individual/collective toggle with participant color encoding and opacity fade
- Myth generation module (`app/myth.py`) with PROHIBITED_WORDS enforcement
- `/myth` POST endpoint wired
- compute_xs and event_count wired into Telegram and Granola pipelines (DEC-014)
- New files: `scripts/__init__.py`, `scripts/backfill_xs.py`, `tests/test_myth.py`

**Sprint 2 deferred items that may affect Sprint 3 scope:**
- Telegram webhook not delivering events — infrastructure config issue (not code bug)
- The Gate (0.12) and The Silence (0.15) xs overlap at low density — design review with Jessie
- Esc key hotkey for closing slide-out panel
- Participant toggle fade should animate smoothly rather than snap instantly
- Archetype panel lacks clickable event items for reverse chaining (archetype→event navigation)
- DEF-016: seed_clusters.py does not populate glyph_id column

### Sprint 3 — Integration Testing + Edge City Demo Prep ✓
**Status:** Complete (7 sessions, tests 125 → 147)

**Delivered:**
- ~393 events seeded from 2 Granola transcripts across 6 clusters
- Batch seeding tool (`scripts/seed_transcript.py`) with speaker remapping, min-length filtering, dry-run, `--date` arg
- 6 deferred items resolved: DEF-010 (atomic RPC), DEF-011, DEF-012, DEF-013, DEF-014, DEF-016
- Myth prompt refined for ancestral register quality (FF-005)
- Frontend demo polish: strata view time axis, loading/empty states (FF-006)
- `event_date` column added to events pipeline and API response (DEC-015, DEC-016)
- XS_CENTERS overlap fixed (Gate/Silence)
- New files: `scripts/seed_transcript.py`, `tests/test_seed_transcript.py`, `scripts/test_myth_quality.py`

### Sprint 4 — Design Brief Alignment (Phase 2)
**Scope:** Visual polish. Implement the Design Brief's aesthetic: Cormorant Garamond / DM Mono typography, river-at-night color palette (#0e0c09 void, #c49a3a gold, #8a8aaa violet-slate), grain overlay, blur and atmosphere, the layering rules. Scroll/zoom/pan on both views.

### Sprint 5 — Zamani View + Scroll/Zoom (Phase 2)
**Scope:** Build the third view (zamani): force-directed archetype-level field with truth threads between related archetypes. Implement scroll/zoom/pan across all views. Mobile layout optimization.

### Sprint 6+ — Truth & Myth Layers (Phase 3)
**Scope:** Layer 3 truth candidate generation. Accept/reject/revise mechanic. Layer 4 full myth output. The publication frame.

## Deferred Items

| ID | Item | Deferred To | Reason |
|----|------|-------------|--------|
| DEF-001 | Google Calendar integration | Phase 2+ | Telegram is lower friction for v1 |
| DEF-002 | Voice memo + Whisper transcription | Phase 2+ | Adds pipeline complexity |
| DEF-003 | Dynamic clustering (HDBSCAN/k-means) | Phase 2+ | Seed clusters sufficient for MVP |
| DEF-004 | Moon nodes (unaffiliated events) | Sprint 4+ | Specified but not critical for MVP |
| DEF-005 | New event arrival animation | Sprint 4+ | Polish, not core functionality |
| DEF-006 | Mobile layout | Sprint 5 | Desktop-first for MVP |
| DEF-007 | Visual myth layer (image generation) | Phase 3+ | Held per Project Bible §14 |
| DEF-008 | Name decision (Sasa/Zamani/compound/other) | Phase 2 | Revisit after prototype validated |
| DEF-009 | Onboarding flow for new users | Phase 4 | Three known users for MVP |
| DEF-015 | Privacy flag (AI-readable, participant-hidden) | Phase 4 | Trust-based for three collaborators |
| DEF-017 | Myth post-validation | Sprint 4+ | Verify generated myths pass PROHIBITED_WORDS and register checks |
| DEF-018 | Transcript dedup | Sprint 4+ | Prevent re-seeding same transcript |
| DEF-019 | LLM-generated event labels | Sprint 4+ | Currently raw text[:80]; Claude summary would improve readability |

## Fast-Follow Feature Ideas

Proposed additions identified during bootstrap. Not part of the original ideation documents. To be evaluated by the full team after MVP ships. Ordered by estimated impact-to-cost ratio.

### FF-001: Dialogue with Your Archetypes
Open a conversational mode from the archetype panel — ask a constellation a question and Claude responds *as* that archetype, drawing exclusively from the cluster's events, speaking in the ancestral register. The past becomes a conversational partner, not a display. Literally "in dialogue with the ancestors of your mind" (Granola transcript). Architecturally simple (one new endpoint, a system prompt, chat UI inside the archetype panel). Prompt engineering is the hard part — Emma should own the voice.

### FF-002: Thematic Segmentation of Conversation Transcripts
Instead of splitting Granola transcripts on speaker turns (too thin to embed meaningfully), use Claude to segment conversations into thematic units before embedding. Each thematic segment becomes one event, attributed to all participating speakers. Preserves the intersubjective quality of insights that emerge *between* speakers. Dramatically improves clustering quality for conversational input. One Claude API call per transcript as a pre-processing step.

### FF-003: Tidal Return as Engagement Mechanism (Resonance Notifications)
When a new Telegram event clusters with an old constellation (high similarity + high time gap), the bot replies in the ancestral register: "Something you said today woke a constellation from the depths." The pool speaks back through the same channel the user is already in. Extends to a weekly "resonance report" summarizing what stirred, which constellations grew, which old ones resurfaced. Solves the habit loop problem (RSK-003) without adding a new surface. Scheduled job (cron) for weekly report.

### FF-004: Seed Pool from Existing Life Data
Bulk upload of journals, message exports, old calendars to pre-populate the pool. Eliminates the empty-pool first-visit problem. The first encounter — seeing constellations you didn't know existed in your own life — demonstrates the tool's value before the daily input habit forms. For MVP demo: pre-seed with the Mar 17 Granola transcript so the map isn't empty on first visit. Uses the same embedding/clustering pipeline.

### FF-005: LLM-Generated Event Labels (DEF-019)
Event labels currently use raw `text[:80]` — the first 80 characters of the message. Replace with a Claude-generated 3-5 word summary that captures the event's essence. One API call per event at ingestion time. Low cost, high readability improvement for both the strata view and detail panels. Identified during Sprint 3 S2 live run.

### FF-006: Myth as Shareable Artifact
A share button on the archetype panel generates a designed standalone card — myth text in Cormorant Garamond, archetype glyph, constellation color signature, the line "Here's a true story that never happened." Something that travels beyond the tool. The Deutsch "reach" test made operational. Server-side renderer (HTML-to-image or template). The moment the tool produces something that is for anyone, not just the user.
