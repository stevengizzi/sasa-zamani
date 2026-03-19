# Risk Register

> Tracked assumptions, risks, and their mitigations.
> Format: RSK-NNN entries.

---

**RSK-001:** Embedding quality insufficient for meaningful clustering
**Date:** 2026-03-18
**Severity:** Low (downgraded from High — Sprint 1)
**Likelihood:** Low

**Risk:**
OpenAI text-embedding-3-small may not produce clusters that feel "surprising and true" on short, informal Telegram messages. The quality of constellation formation is the entire user experience — if events cluster in ways that feel arbitrary or overly broad, the tool fails its core promise.

**Sprint 1 Validation:**
- Centroid similarity matrix computed: healthy spread 0.25–0.49, mean 0.33
- Cluster sanity test: 6/6 messages assigned to correct archetype
- Similarity scores ranged from 0.42 (The Silence) to 0.76 (What the Body Keeps)
- All scores above the default 0.3 CLUSTER_JOIN_THRESHOLD
- Default threshold of 0.3 is well-calibrated against the centroid matrix

**Sprint 3 Observation:**
- With ~393 real events seeded from 2 Granola transcripts, most events are assigned to clusters with cosine similarity below the 0.3 threshold. This is because seed cluster centroids were computed from tags, not from the embedding model. The embeddings themselves are high quality, but the centroids are misaligned with the embedding space. Centroid recomputation from actual member event embeddings is the primary mitigation path and would likely resolve the low-similarity assignments.

**Mitigation:**
1. ~~Test embedding quality early (Sprint 1) with real messages from the team before building the full pipeline.~~ Done.
2. ~~JOIN_SIM threshold tuning session with real data.~~ CLUSTER_JOIN_THRESHOLD=0.3, validated.
3. Centroid recomputation from member event embeddings (deferred — next priority for clustering quality).
4. Fallback: Cohere embed-multilingual-v3 if OpenAI produces poor results.
5. Longer-term fallback: local sentence-transformers with fine-tuning on the team's actual data.

**Owner:** Steven
**Related:** DEC-003, DEC-011

---

**RSK-002:** Myth generation quality — fable risk
**Date:** 2026-03-18
**Severity:** Medium (downgraded from High — Sprint 2)
**Likelihood:** Medium

**Risk:**
Claude's mythic sentence output may default to therapy-speak, generic wisdom, or explicit moral statements (fable) rather than the ancestral, felt, non-extractable register the project requires. The Project Bible's critical distinction: "if you can read it and immediately extract one clean propositional truth, it's probably a fable." The current prototype prompt works reasonably well but sometimes produces generic outputs.

**Sprint 2 Implementation:**
- Myth module implemented in `app/myth.py` with `build_myth_prompt`, `should_regenerate`, `generate_myth`, `get_or_generate_myth`
- PROHIBITED_WORDS constant enforces banned word list: journey, growth, explore, reflect, transformation, powerful, detect, discover, reveal, activate, unlock
- Prompt instructs Claude to speak in ancestral register — from the past looking forward
- Caching with delta-based regeneration (3+ new events triggers refresh)

**Sprint 3 Refinement:**
- Myth prompt tuned in S3 session for improved ancestral register quality, reduced therapy-speak
- Tested against real cluster data (~393 seeded events across 6 clusters)
- DEF-017 (myth post-validation) identified as carry-forward — automated PROHIBITED_WORDS checking of generated output not yet implemented
- Full prompt review with Emma still needed for tonal sign-off

**Mitigation:**
1. ~~Prompt engineering sprint with Emma (who owns the tonal register) before launch.~~ Partially addressed: PROHIBITED_WORDS list implemented. Full prompt review with Emma still needed.
2. ~~Banned word list enforced in the prompt.~~ Done — PROHIBITED_WORDS in `app/myth.py`.
3. A/B testing: generate 3 myth candidates per cluster, let the team select the best. Use selections to refine the prompt.
4. The embarrassment test from the Project Bible: "A good truth could not have been generated without this person's data." Apply as a quality gate.

**Owner:** Emma (tone), Steven (implementation)
**Related:** DEC-010

---

**RSK-003:** The habit loop problem — no day-2 retention mechanism
**Date:** 2026-03-18
**Severity:** High
**Likelihood:** High

**Risk:**
There is no clear answer to "what makes someone come back on day 2." The tool requires sustained input over time to produce meaningful constellations. A single day's entries are too sparse for the system to surface surprising patterns. If users don't develop a regular practice of sending events to the Telegram bot, the pool stays shallow and the tool fails to demonstrate its value.

**Mitigation:**
1. The MVP is for three committed collaborators who are already philosophically invested. The habit loop problem is less acute for v1 than for public launch.
2. Design a "first session" experience that produces at least one constellation and one mythic sentence from initial data — seed the pool with the team's existing Granola transcript so it's not empty on first visit.
3. The Telegram bot could send a daily prompt (drawn from the recording protocol prompts in the Project Bible: "What moment today felt strange or out of place?") — but only if the team wants it. Notification fatigue is a risk.
4. Defer the full habit-loop design to post-MVP. For now, rely on the team's intrinsic motivation and the Edge City context (dense shared experience creates natural input).

**Owner:** All three
**Related:** DEC-006, DEC-007

---

**RSK-004:** Frontend rebuild scope creep
**Date:** 2026-03-18
**Severity:** Medium
**Likelihood:** High

**Risk:**
The current prototype (sasa_zamani_v3.html) is ~1100 lines of tightly coupled canvas code with mocked data. Replacing the data layer (from hardcoded JS objects to API calls) while preserving both views, the animated transition, the panel system, and the archetype glyphs is a non-trivial refactor. Scope creep risk: "while I'm in here, I might as well also fix/add X."

**Mitigation:**
1. Define a strict scope for the frontend refactor in Sprint 1: replace data source, preserve existing interactions, add collective toggle. Nothing else.
2. Visual polish, new features, and the design brief's aesthetic refinements (grain overlay, Cormorant Garamond, etc.) are Sprint 2+.
3. The strata and resonance views already work. Don't rewrite them — adapt them.

**Owner:** Steven
**Related:** DEC-005, DEC-009

---

**RSK-005:** API key exposure
**Date:** 2026-03-18
**Severity:** Medium
**Likelihood:** Low (if handled correctly)

**Risk:**
The current prototype calls the Claude API directly from the browser with a visible API key. The deployed v1 must not expose OpenAI, Anthropic, or Telegram bot tokens to the client.

**Mitigation:**
1. All API calls (embedding, myth generation, Telegram webhook) go through the FastAPI backend. Environment variables on Railway hold the keys. The frontend never touches an API key.
2. Standard practice — low risk if followed from Sprint 1.

**Owner:** Steven
**Related:** DEC-001, DEC-004

---

**RSK-006:** Granola transcript parsing fragility
**Date:** 2026-03-18
**Severity:** Low
**Likelihood:** Medium

**Risk:**
The Granola transcript format (plain text with "Speaker A/B/C:" labels) may change between versions, or different export formats may produce different structures. The parser could break silently, producing misattributed or malformed events.

**Mitigation:**
1. Build the parser to handle the known format and fail loudly on unexpected input.
2. Add a manual review step: after upload, show the parsed events to the user for confirmation before they enter the pool.
3. Map speaker labels to participant names at upload time (user selects: "Speaker A = Emma, Speaker B = Jessie, Speaker C = Steven").

**Owner:** Steven
**Related:** DEC-006

---

**RSK-007:** Philosophical coherence under implementation pressure
**Date:** 2026-03-18
**Severity:** Medium
**Likelihood:** Medium

**Risk:**
The project has an unusually strong philosophical foundation (Mbiti, Campbell, Deutsch, Popper, the myth-vs-fable distinction, decay as delivery mechanism). Under MVP time pressure, implementation shortcuts may violate philosophical principles — e.g., adding a chronological list view "for convenience," using the word "discover" in UI copy, generating fables instead of myths, treating the pool as a dashboard rather than a river.

**Mitigation:**
1. The Design Brief (§07 "What to Avoid") and the Project Bible (§11 "Language & Branding" and §12 "What We're Not") are explicit guardrails. Reference them in sprint reviews.
2. Emma is the tonal guardrail. No UI copy or Claude prompt ships without her review.
3. The single test from the Design Brief: "Does it feel like the diagram of something that can't quite be diagrammed?"

**Owner:** Emma (tone/philosophy), Steven (implementation discipline)
**Related:** DEC-010, DEC-009

---

**RSK-008:** Three-person team with no redundancy
**Date:** 2026-03-18
**Severity:** Low
**Likelihood:** Low

**Risk:**
Steven is the sole developer. If Steven is unavailable, development stops. Jessie and Emma contribute design, copy, and thematic guidance but cannot implement.

**Mitigation:**
1. The two-Claude architecture (DEC-008) and well-documented canon documents mean a new developer could onboard from the docs.
2. For MVP, this is an accepted risk. The team is small and committed.
3. Jessie has demonstrated ability to work with Claude on prototype iterations — she could potentially handle frontend refinements with Claude Code guidance if needed.

**Owner:** Steven
**Related:** DEC-008

---

**RSK-009:** Cluster concentration when seed archetypes don't match incoming content type
**Date:** 2026-03-20
**Severity:** Medium
**Likelihood:** Medium

**Risk:**
Seed archetypes (The Gate, What the Body Keeps, The Table, The Silence, The Root, The Hand) were designed for personal lived-experience events (Telegram messages about daily life). When the input is intellectual discussion (e.g., Granola transcripts of philosophical conversations), most events fall below the join threshold for all seed clusters and concentrate in a single dynamic cluster. Sprint 4 re-seed: 28/29 events from 2 Granola transcripts assigned to one dynamic cluster ("The Argot").

**Sprint 4 Observation:**
- After significance filtering reduced the event count from 48 to 29, nearly all remaining events (intellectual discussion content) were assigned to a single dynamic cluster
- Seed archetypes cover experiential domains (dream, body, food, silence, memory, writing) but not cognitive/dialogical domains (argument, inquiry, conceptual exploration)
- This is not a failure of the clustering pipeline — the embeddings and similarity math are working correctly — but a mismatch between seed archetype coverage and input content type

**Mitigation:**
1. Expand seed archetypes to cover intellectual/discussion content (e.g., "The Argument," "The Inquiry," "The Forge"). Requires team input on which archetypes to add.
2. Accept that dynamic clustering will handle content types that seeds don't cover — this is the designed fallback path (DEC-011, DEC-023).
3. Monitor cluster distribution after each re-seed or significant data addition.

**Owner:** Steven (implementation), Jessie + Emma (archetype design)
**Related:** DEC-011, DEC-023, RSK-001
