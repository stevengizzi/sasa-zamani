# Decision Log

> All architectural and process decisions, logged at the time they are made.
> Format: DEC-NNN entries.

---

**DEC-001:** Python + FastAPI for backend
**Date:** 2026-03-18
**Sprint:** Bootstrap

**Decision:**
Use Python with FastAPI as the backend framework for the Sasa/Zamani server.

**Alternatives Rejected:**
1. Node.js + Express: Weaker embedding ecosystem. Would require shelling out to Python for sentence-transformers or numpy/scipy similarity math. The Telegram bot library is comparable in both ecosystems, but the ML pipeline tips the balance decisively toward Python.
2. Django: Too heavy for this API surface. Sasa/Zamani needs a thin API layer (5-6 endpoints), not a full MVC framework with ORM, admin, and template engine.
3. Flask: FastAPI is strictly better for this use case — native async, automatic OpenAPI docs, type hints with Pydantic validation.

**Rationale:**
The embedding pipeline (vector generation, cosine similarity, cluster assignment) is the core computational task of the backend. Python's ecosystem for this (OpenAI SDK, sentence-transformers, numpy, scipy, scikit-learn for clustering) is unmatched. FastAPI adds async request handling, which matters for concurrent Claude API myth generation calls, and auto-generated API docs that help non-developer team members (Jessie, Emma) understand the system.

**Constraints:**
Steven is sole developer. MVP target is one week. The embedding pipeline is non-negotiable for v1 (tag-based Jaccard insufficient for real natural-language input).

**Supersedes:** N/A
**Cross-References:** DEC-003 (embedding model), DEC-004 (deployment)

---

**DEC-002:** Supabase (Postgres + pgvector) for database
**Date:** 2026-03-18
**Sprint:** Bootstrap

**Decision:**
Use Supabase as the managed database, leveraging Postgres with the pgvector extension for embedding storage and similarity queries.

**Alternatives Rejected:**
1. SQLite + local file: No vector similarity support without additional libraries. Not accessible from multiple devices. Would require migration later.
2. MongoDB: Document store doesn't add value here — the data model is relational (events belong to participants, events belong to clusters). No native vector similarity.
3. Pinecone / Weaviate (dedicated vector DB): Overkill. The event count for three participants over weeks/months is in the hundreds to low thousands — Postgres with pgvector handles this trivially. Adding a separate vector DB creates unnecessary infrastructure complexity.
4. Self-hosted Postgres: Adds ops overhead (backups, upgrades, monitoring) that Supabase eliminates. Free tier is sufficient for prototype scale.

**Rationale:**
Supabase provides managed Postgres with pgvector, realtime subscriptions (useful for live pool updates when new events arrive), a generous free tier, and a REST API that can be used directly from the frontend if needed. Cluster assignment can be computed with a SQL query (`ORDER BY embedding <=> $1 LIMIT 1`) rather than in application code. The schema is simple (events table with vector column) and the scale is small.

**Constraints:**
Three participants, hundreds of events over weeks. No budget for managed services beyond free tiers.

**Supersedes:** N/A
**Cross-References:** DEC-001 (backend stack), DEC-003 (embedding model — determines vector dimensionality)

---

**DEC-003:** OpenAI text-embedding-3-small for v1 embeddings
**Date:** 2026-03-18
**Sprint:** Bootstrap

**Decision:**
Use OpenAI's text-embedding-3-small model (1536 dimensions) for semantic embedding of event text in v1. Preserve a clean swap path to local models (sentence-transformers) for future iterations.

**Alternatives Rejected:**
1. Tag-based Jaccard similarity (current prototype): Functional for mocked data with pre-assigned tags, but fails on real natural-language input. Users won't tag their Telegram messages — the embedding must handle raw text. This is a v1 requirement, not a nice-to-have.
2. Local sentence-transformers (all-MiniLM-L6-v2): Eliminates API dependency and is better for privacy long-term, but adds deployment complexity (model weights ~80MB, CPU inference latency, memory footprint on Railway). Not worth the overhead for MVP week. Swap path preserved — the embedding call is a single function that returns a vector; everything downstream is model-agnostic.
3. Cohere embed-multilingual-v3: Stronger multilingual support. Keep as fallback if Jessie's Hakka/Chinese-language entries cluster poorly with OpenAI. Not the default because OpenAI's model is sufficient for the expected input (primarily English with occasional multilingual fragments).

**Rationale:**
text-embedding-3-small is fast (<100ms per call), cheap ($0.02/million tokens — under $1 for thousands of events), produces 1536-dimensional vectors with strong semantic coverage for short-to-medium text, and has a mature Python SDK. The quality is more than sufficient for Telegram messages and Granola transcript segments.

**Constraints:**
Requires OpenAI API key. Adds external dependency. Acceptable for MVP; revisit for production if privacy or cost becomes a concern at scale.

**Supersedes:** N/A
**Cross-References:** DEC-002 (pgvector stores 1536-dim vectors), DEC-001 (Python SDK)

---

**DEC-004:** Railway for deployment
**Date:** 2026-03-18
**Sprint:** Bootstrap

**Decision:**
Deploy the backend on Railway with a public HTTPS URL. Supabase remains cloud-hosted (separate from Railway).

**Alternatives Rejected:**
1. Localhost only: The team will soon be geographically distributed. A local-only deployment doesn't survive the week. Also inadequate for showing at Edge City gathering — attendees need a URL they can visit.
2. Render: Slightly slower cold starts than Railway. Otherwise equivalent. Railway's GitHub-push-to-deploy workflow is marginally smoother.
3. Fly.io: More powerful (edge deployment, persistent volumes) but more configuration overhead. Overkill for a FastAPI app serving three users.
4. Vercel: Excellent for frontend, awkward for a Python backend with a long-running Telegram webhook handler.

**Rationale:**
Railway provides a public URL with HTTPS, deploys from GitHub (push to main → auto-deploy), supports environment variables for API keys (OpenAI, Anthropic, Telegram bot token, Supabase credentials), and has a free tier sufficient for MVP. The FastAPI app cold-starts in under 2 seconds.

**Constraints:**
Must be accessible from multiple devices and locations. Must support environment variables for secrets. Must not require DevOps expertise to maintain.

**Supersedes:** N/A
**Cross-References:** DEC-001 (Python/FastAPI), DEC-002 (Supabase cloud DB)

---

**DEC-005:** Frontend stays as single HTML/JS canvas file for v1
**Date:** 2026-03-18
**Sprint:** Bootstrap

**Decision:**
The Sasa Map frontend remains a single HTML file with inline JavaScript and canvas rendering. No framework migration for v1.

**Alternatives Rejected:**
1. React + Vite: Would provide component structure, state management, and a proper build pipeline. But migrating the existing ~1100-line canvas prototype to React would consume 2-3 days of MVP time for zero user-facing gain. The current prototype works.
2. Svelte: Same reasoning as React. The migration cost exceeds the benefit at this stage.

**Rationale:**
The current prototype (sasa_zamani_v3.html) has two working views (strata + resonance), archetype panels, spiral data display, side panel navigation, and Claude API integration. Porting this to a framework is a v2 concern. The backend serves it as a static file. When the codebase matures past MVP and needs component reuse, routing, or state management, migrate then.

**Constraints:**
MVP in one week. Sole developer. The prototype already exists and works.

**Supersedes:** N/A
**Cross-References:** DEC-009 (view and interaction requirements that the frontend must satisfy)

---

**DEC-006:** Telegram bot + Granola transcript upload as v1 input modalities
**Date:** 2026-03-18
**Sprint:** Bootstrap

**Decision:**
V1 supports two input modalities: (1) a Telegram bot that receives messages from individuals or a group chat, and (2) a web endpoint for uploading Granola conversation transcripts. Both are processed into the same event format and stored in the same database.

**Alternatives Rejected:**
1. Google Calendar integration: Was explored extensively in Jessie's prototype conversations. Deferred because calendar events are logistically dry without annotations, and the dedicated-calendar workflow adds friction compared to just messaging a Telegram bot. Revisit post-MVP.
2. Manual text entry via web form: Lower priority than Telegram (which the team already uses) and Granola (which captures their group conversations). Can be added trivially later as a POST endpoint.
3. Voice memo upload + Whisper transcription: Valuable but adds pipeline complexity (audio storage, Whisper API calls, transcription latency). Deferred post-MVP.

**Rationale:**
Telegram is where the team already communicates. The bot receives messages in real-time with zero new habit formation required. Granola captures the team's in-person conversations (which are philosophically rich and produce dense meaning-making data, as the Mar 17 transcript demonstrates). Together, these two modalities cover both individual daily entries and collective conversation processing.

Granola integration for v1 is a paste/upload endpoint — the backend parses speaker-labeled text into attributed event segments, embeds each, and stores them. No API integration needed.

**Constraints:**
Telegram bot requires a bot token from @BotFather and a webhook endpoint. Granola transcript format is plain text with speaker labels — parser must handle this format.

**Supersedes:** N/A
**Cross-References:** DEC-007 (participant model), DEC-001 (backend handles both pipelines)

---

**DEC-007:** Individual + small community (3 participants) as v1 scope
**Date:** 2026-03-18
**Sprint:** Bootstrap

**Decision:**
V1 supports individual use as the atomic unit, plus a communal view for three named participants (Jessie, Emma, Steven). The user can toggle between their individual data and the collective pool. All events are attributed to a participant.

**Alternatives Rejected:**
1. Individual-only: Would simplify the data model but forfeits the communal demonstration that is the team's primary proof-of-concept. The Edge City demo requires showing three people's events clustering together.
2. Large-group communal (10+ participants): Introduces scaling, privacy, and moderation challenges that aren't relevant for three trusted collaborators. Deferred.

**Rationale:**
Individual is the atomic level — every event belongs to one person. The communal view is an overlay that shows all participants' events together, with shared constellations (events from multiple participants clustering by semantic resonance) highlighted. Three participants is small enough that privacy controls can be informal (trust-based, not permission-based) and the UI doesn't need participant filtering beyond a simple toggle.

Participant colors (from Jessie's specs): Jessie #7F77DD (purple), Emma #D85A30 (coral), Steven #1D9E75 (teal), Shared #BA7517 (amber gold).

**Constraints:**
Three participants for MVP. The architecture should not preclude scaling to larger groups, but it doesn't need to optimize for it yet.

**Supersedes:** N/A
**Cross-References:** DEC-006 (Telegram bot attributes messages to participants), DEC-009 (collective toggle in views)

---

**DEC-008:** Two-Claude architecture for development workflow
**Date:** 2026-03-18
**Sprint:** Bootstrap

**Decision:**
Use the two-Claude architecture: Claude.ai (this project) for strategic planning, design, review, and documentation. Claude Code for implementation. Git bridges the two.

**Alternatives Rejected:**
1. Claude.ai only: Cannot execute code, run tests, or interact with the filesystem. Implementation would be manual copy-paste from conversation to editor.
2. Claude Code only: Loses the strategic planning layer. Sprint planning, adversarial review, and document management are better suited to the conversational interface.

**Rationale:**
Steven's established workflow (claude-workflow metarepo). Separation ensures each session starts with full context and clear instructions. Claude.ai produces sprint specs and implementation prompts; Claude Code executes them.

**Constraints:**
Requires Steven to manage git as the bridge. Requires canon documents to be kept current so both Claudes have accurate context.

**Supersedes:** N/A
**Cross-References:** All subsequent sprint planning and implementation decisions.

---

**DEC-009:** Sasa Map requires both views, animated transition, and chained panel navigation
**Date:** 2026-03-18
**Sprint:** Bootstrap

**Decision:**
The Sasa Map ships with both the strata view (time × semantic spectrum grid) and the resonance view (cluster-based ring layout), connected by an animated re-sorting transition between them. Both event nodes and archetype names are clickable in both views, each opening their respective slide-out detail panels. Content within panels is internally linked: clicking a resonant neighbor, archetype name, glyph, or related event navigates to that entity's panel (chained navigation).

**Alternatives Rejected:**
1. Single view only: Would reduce implementation scope but sacrifices the two complementary perspectives (chronological-semantic in strata, purely semantic in resonance) that make the tool's meaning-making visible from different angles.
2. Non-interactive panels (display only, no internal linking): Would simplify the UI but breaks the exploratory, discovery-oriented interaction model. The tool's value is in following connections — clicking from an event to its archetype to a resonant neighbor to that neighbor's archetype is the user enacting the meaning-making process.

**Rationale:**
Both views exist and work in the current v3 prototype. The strata view reveals temporal patterns (dense weeks, sparse periods, the accumulation of the past). The resonance view reveals semantic patterns (which events cluster, which archetypes dominate). The animated transition between them is the user experiencing the same data reorganized by a different principle — time vs. meaning. This directly enacts Mbiti's insight that time is organized by resonance, not chronology.

Chained panel navigation is partially implemented in v3 (event panel → archetype panel via glyph click, event panel → neighbor event panel). The commitment is to carry this full interaction model through the rebuild with real data.

**Constraints:**
The transition animation and panel system add frontend complexity. Must be maintained through the migration from mocked data to live data.

**Supersedes:** N/A
**Cross-References:** DEC-005 (frontend stays as HTML/JS canvas), DEC-007 (collective toggle in views)

---

**DEC-010:** Myth generation uses Claude API in ancestral register
**Date:** 2026-03-18
**Sprint:** Bootstrap
Confirmed in Sprint 1.

**Decision:**
Claude (claude-sonnet-4-20250514) generates mythic sentences for archetype clusters. The prompt instructs Claude to speak in an ancestral register — from the past looking forward, naming the thread that runs through the events, not summarizing or analyzing them. Max tokens: 80. Results cached per cluster; regenerated when cluster composition changes significantly (3+ new events).

**Alternatives Rejected:**
1. No AI-generated text: The mythic sentence is what transforms a cluster of dots into a named archetype with felt meaning. Without it, the visualization is an interesting graph but not a meaning-making tool.
2. GPT-4o for myth generation: Claude's voice is better suited to the register. The existing prompt (tested in prototype) works well with Claude. Team familiarity with Anthropic ecosystem.

**Rationale:**
The myth prompt from the current prototype is working well: "Write one sentence (20-35 words) in an ancestral register that names what this cluster is actually about — what thread runs through all these moments. Speak as if from the past looking forward." Claude calls move server-side in the rebuild (DEC-001 backend holds the API key). Caching prevents redundant calls and reduces latency.

**Constraints:**
Requires Anthropic API key. Myth quality depends on prompt engineering — must be tested against the language brief (design brief §06). Banned words: journey, growth, explore, reflect, transformation (unless earned), powerful.

**Supersedes:** N/A
**Cross-References:** DEC-001 (server-side proxy), DEC-005 (frontend calls /myth endpoint)

---

**DEC-011:** Archetype clustering uses seed clusters initially, dynamic clustering deferred
**Date:** 2026-03-18
**Sprint:** Bootstrap
Confirmed in Sprint 1.

**Decision:**
V1 uses seed clusters: the six named archetypes from the prototype (The Gate/dream, What the Body Keeps/body, The Table/food, The Silence/silence, The Root/memory, The Hand/writing) serve as initial cluster centroids. New events are assigned to the nearest seed cluster by cosine similarity. Archetype names are regenerated by Claude when cluster composition changes significantly. Fully dynamic clustering (k-means, HDBSCAN) is deferred.

**Alternatives Rejected:**
1. Fully dynamic clustering from day one: More philosophically honest (let patterns emerge) but harder to tune, produces unstable cluster counts, and makes archetype naming unpredictable. Higher risk for MVP.
2. Fixed clusters with no new clusters allowed: Too rigid. Real data will produce patterns that don't map to the initial six. The system must allow new clusters to form when an event doesn't fit any existing seed above a similarity threshold.

**Rationale:**
Seed clusters provide stability and legibility for the MVP demo. The six archetypes are thematically grounded (drawn from Jessie's personal data territory) and cover a reasonable range of human experience. New clusters can emerge when events fall below the JOIN_SIM threshold for all existing seeds — the system creates a new unnamed cluster and requests a Claude-generated archetype name. This hybrid approach gives the stability of seeds with the flexibility of emergence.

**Constraints:**
JOIN_SIM threshold must be tuned against real data. The seed centroids need to be recomputed from the new embedding model (they were originally tag-based).

**Supersedes:** N/A
**Cross-References:** DEC-003 (embedding model), DEC-010 (Claude generates archetype names)

---

**DEC-012:** Raw JSON webhook over python-telegram-bot
**Date:** 2026-03-18
**Sprint:** 1
**Session:** S4a

**Decision:**
Handle raw Telegram webhook JSON directly rather than using python-telegram-bot's Update model.

**Alternatives Rejected:**
1. python-telegram-bot Update.de_json(): Adds framework coupling for a webhook-only receiver. The bot library is designed for polling mode with handlers; we only need to extract text, username, and update_id from a JSON payload.

**Rationale:**
Telegram sends plain JSON. Manual parsing is ~10 lines of dict.get() calls. Avoids importing and initializing the bot framework just to deserialize a webhook payload. python-telegram-bot remains in requirements.txt as a future option if bot-side features (inline keyboards, reply markup) are needed.

**Supersedes:** N/A
**Cross-References:** DEC-006 (Telegram as v1 input)

---

**DEC-013:** In-memory dedup for Telegram updates
**Date:** 2026-03-18
**Sprint:** 1
**Session:** S4a

**Decision:**
Use an in-memory Python set for Telegram update_id deduplication.

**Alternatives Rejected:**
1. Database-based dedup (query events table for matching update_id): Adds a DB read to every incoming message. Correct for multi-worker deployments but unnecessary overhead for v1 single-process.
2. Redis-based dedup: Introduces a new infrastructure dependency for a problem that doesn't exist at v1 scale.

**Rationale:**
Single-process Railway deployment means one Python process handles all requests. An in-memory set is O(1) lookup, zero-dependency, and sufficient. The set does not survive process restarts, but Telegram re-delivery + idempotent DB upsert makes this safe. Switch to DB-based dedup if scaling to multiple workers.

**Supersedes:** N/A
**Cross-References:** DEC-004 (Railway deployment), DEF-013 (unbounded set growth)

---

**DEC-014:** Lift do-not-modify constraint on telegram.py and granola.py
**Date:** 2026-03-19
**Sprint:** 2
**Session:** Pipeline Fix (impromptu)

**Decision:**
Lifted the do-not-modify constraint on telegram.py and granola.py for a targeted pipeline wiring fix (compute_xs + event_count verification).

**Alternatives Rejected:**
1. Deferring to Sprint 3: Would leave broken behavior deployed — myth caching wouldn't work and xs values wouldn't be computed for new events.
2. Backfill-only workaround: Doesn't fix the live pipeline. New events arriving via Telegram or Granola would still lack xs values and wouldn't trigger event_count increments.

**Rationale:**
Sprint 2 planning placed telegram.py and granola.py on the do-not-modify list to protect the input pipeline during frontend migration. By the time this fix was needed, frontend migration was complete and verified. The fixes were additive only — adding `compute_xs()` and `increment_event_count()` calls to existing flows, no restructuring. The constraint had served its purpose (protecting the input pipeline while the frontend was being migrated) and was no longer load-bearing.

**Constraints:**
Frontend migration must be complete and verified before modifying input pipeline files. Fixes must be additive only (no restructuring).

**Supersedes:** N/A
**Cross-References:** DEC-006 (input modalities), DEF-010 (non-atomic increment)
