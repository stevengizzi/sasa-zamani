# Sprint 3: Integration Testing + Edge City Demo Prep

## Goal

Populate the Sasa Map with real data from two Granola transcripts, clear the accumulated backend deferred-item backlog, tune myth generation quality, and polish the frontend for the Edge City demo (~Mar 22). By sprint end, three participants can send Telegram messages and see them appear in a map already rich with seeded conversation data.

## Scope

### Deliverables

1. **Backend deferred-item cleanup** — resolve DEF-010, DEF-011, DEF-012, DEF-013, DEF-014, DEF-016, and the Gate/Silence xs overlap. All six open backend-scoped deferred items closed.
2. **Granola transcript seeding (FF-004)** — a script that seeds the production database with the March 17 and March 18 Granola transcripts, with per-transcript speaker mapping and minimum segment length filtering. Map is populated with ~393 real events across all six archetypes.
3. **Myth prompt refinement** — improved `build_myth_prompt` that produces output passing the Design Brief's tonal test ("marginalia in an old book") with real cluster data. Thin-cluster (≤2 events) handling. Manual quality testing script.
4. **Frontend demo polish** — Esc key panel close, archetype→event reverse chaining, smooth fade animation on participant toggle, basic loading state for initial data fetch.
5. **Integration verification** — documented end-to-end demo walkthrough confirming the full flow works: Telegram → map → panels → myth.

### Acceptance Criteria

1. **Backend cleanup:**
   - `insert_cluster` accepts optional `glyph_id` parameter and persists it to DB
   - `seed_clusters()` passes `glyph_id` from SEED_ARCHETYPES to `insert_cluster`
   - `increment_event_count` uses a single SQL UPDATE (no read-then-write)
   - `scripts/seed_clusters.py` imports SEED_ARCHETYPES from `app/clustering` (no duplication)
   - `_processed_update_ids` set in `telegram.py` is capped at 10,000 entries
   - `process_granola_upload` returns actual cluster name (not cluster_id) in the `cluster_name` field
   - `XS_CENTERS` for The Gate = 0.08, The Silence = 0.20 (≥0.10 separation)
   - All existing tests still pass (≥122 pass, ≤3 skip)

2. **Transcript seeding:**
   - `scripts/seed_transcript.py` exists and runs without error
   - March 17 speaker mapping: A→steven, B→emma, C→jessie
   - March 18 speaker mapping: B→emma, C→jessie, F→steven, all others→shared
   - Segments shorter than 100 characters are filtered out
   - Dry-run mode prints planned uploads without touching the database
   - After seeding, the map loads with ≥50 real events (conservative lower bound; expected ~393)
   - Events are distributed across multiple clusters (not all in one)

3. **Myth prompt:**
   - `build_myth_prompt` includes register guidance from Design Brief copy tone section
   - `build_myth_prompt` includes embarrassment test instruction
   - Thin-cluster variant triggers when event count ≤ 2
   - No PROHIBITED_WORDS appear in generated myth output (existing enforcement preserved)
   - Myth output for ≥3 clusters reviewed and documented as passing tonal test

4. **Frontend polish:**
   - Pressing Esc closes any open slide-out panel
   - Clicking an event name in the archetype detail panel opens that event's detail panel
   - Participant toggle opacity change animates smoothly (CSS transition, not instant snap)
   - Initial page load shows a loading indicator until `/events` and `/clusters` return

5. **Integration verification:**
   - `demo-verification.md` documents a successful end-to-end walkthrough
   - Walkthrough covers: Telegram message → event in map → event panel → archetype panel → myth display → reverse chain → toggle → Esc close
   - No blocking errors during walkthrough

### Performance Benchmarks

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| Frontend load time (with seeded data) | < 5s on broadband | Manual timing in Chrome DevTools |
| `/events` response time (~400 events) | < 2s | curl timing against production |
| `/clusters` response time | < 500ms | curl timing against production |

### Config Changes

No config changes in this sprint.

## Dependencies

- Sprint 2 complete: frontend migration, myth module, participant colors, chained panels — all done
- Telegram webhook functional — confirmed working
- Production Supabase accessible for seeding script
- OpenAI API available for embedding ~400 transcript segments
- Anthropic API available for myth generation testing
- Both Granola transcripts committed to repo (`docs/source/3-17-granola-transcript.md`, `docs/source/3-18-granola-transcript.md`)

## Relevant Decisions

- DEC-005: Frontend stays HTML/JS canvas — no framework migration. All S4 work is in `static/index.html`.
- DEC-010: Claude myth generation in ancestral register — S3 refines the prompt, doesn't change the architecture.
- DEC-011: Seed clusters, dynamic deferred — no new archetypes this sprint.
- DEC-012: Raw JSON webhook — Telegram pipeline untouched except dedup cap (DEF-013).
- DEC-013: In-memory dedup — S1b adds size cap, doesn't change mechanism.
- DEC-014: Lifted do-not-modify on telegram.py/granola.py — both are modified in S1b.

## Relevant Risks

- RSK-002: Myth generation fable risk — S3 directly addresses this with prompt refinement. Severity may be updated based on results.
- RSK-004: Frontend rebuild scope creep — S4 scope is strictly bounded (4 features, no layout changes, no style changes).
- RSK-007: Philosophical coherence under implementation pressure — myth prompt refinement must hold to the ancestral register. The Design Brief and Project Bible are the quality gates.

## Session Count Estimate

5 development sessions + 1 contingency (visual-review fixes) + 1 verification session = 7 total.
Rationale: Each session scores ≤13 on compaction risk. The backend cleanup splits into two sessions because touching 4+ files in one pass exceeds the threshold. Frontend session is low-risk but gets a fix contingency slot because visual work is inherently harder to get right on the first pass.
