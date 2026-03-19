# Sprint 4: Data Quality + Significance Filtering

## Goal
Improve data quality across both ingestion pipelines so the Sasa Map shows meaningful constellations instead of a catch-all Table cluster. Filter insignificant content before it becomes an event, store all raw inputs for provenance, redesign labels for a marginalia register, implement the designed-but-unbuilt new-cluster creation path (DEC-011), and fix the 10,243-char truncation bug (DEF-021).

## Scope

### Deliverables

1. **Significance filtering** — Add a significance score (0.0–1.0) to the segmentation prompt and the Telegram label prompt. Segments/messages below `significance_threshold` (configurable, default 0.3) are stored in `raw_inputs` but not promoted to events. Score ≥ threshold passes; strictly below is excluded.

2. **Raw input storage** — New `raw_inputs` table storing all incoming data: Granola transcripts as full text (one row per upload), Telegram messages as individual rows (one row per message). Events get a nullable `raw_input_id` FK plus `start_line`/`end_line` (nullable, used by Granola segments only). Below-threshold content is always accessible via the stored raw input.

3. **Better labels** — Redesign the label prompt for both pipelines. Target register: a scholar's notebook margin note — precise, evocative, never vague keyword extraction. 4–8 words. Should read like a proposition, not a tag cloud. "Nakedness as awareness of mortality" not "Garden Eden Fall Naked."

4. **Duplicate label defense** — Two layers: (a) intra-transcript: the segmentation prompt instructs Claude to produce unique labels, (b) post-processing: after all labels are generated for a batch, a dedup function appends ordinal suffixes (e.g., "(II)") to any duplicates.

5. **Below-threshold new archetype creation** — When `assign_cluster()` finds best similarity < `cluster_join_threshold`, create a new cluster instead of force-assigning. New cluster gets the event's embedding as initial centroid, `is_seed=false`, and placeholder name "The Unnamed." When a cluster reaches `archetype_naming_threshold` events (configurable, default 3), Claude generates an archetype name in the project's register. Centroids list is refreshed after new cluster creation so subsequent events in the same batch can join it.

6. **DEF-021 truncation fix** — Investigate and fix the 10,243-char truncation that cuts three segments mid-sentence. Trace through the pipeline to find the limit.

### Acceptance Criteria

1. **Significance filtering:**
   - Segmentation prompt returns a `significance` field (float 0.0–1.0) per segment
   - `generate_event_label()` returns both label and significance score
   - Segments/messages with significance < threshold are not inserted into events table
   - Below-threshold content is still stored in raw_inputs
   - `significance_threshold` is configurable via environment variable
   - Known noise segments ("Session Ending Voice Identification", "Technical audio video setup") score below threshold when re-seeded

2. **Raw input storage:**
   - `raw_inputs` table exists with columns: id (UUID), text (TEXT), source (TEXT), source_metadata (JSONB), created_at (TIMESTAMPTZ)
   - Events table has nullable columns: raw_input_id (UUID FK), start_line (INT), end_line (INT)
   - Granola upload stores full transcript in raw_inputs before segmentation
   - Telegram pipeline stores every message in raw_inputs before significance check
   - Events created from Granola segments have valid raw_input_id, start_line, end_line
   - Events created from Telegram have valid raw_input_id, null start_line/end_line

3. **Better labels:**
   - Labels read as propositions, not keyword lists
   - Labels are 4–8 words
   - No ALL-CAPS keyword style labels in re-seeded data
   - Both segmentation prompt and Telegram label prompt use the marginalia register instruction

4. **Duplicate label defense:**
   - Segmentation prompt includes uniqueness instruction
   - Post-processing dedup function exists and appends " (II)", " (III)" etc. to duplicates
   - No exact-duplicate labels in re-seeded data

5. **Below-threshold archetype creation:**
   - Events with best similarity < cluster_join_threshold create a new cluster
   - New cluster has is_seed=false, centroid = event embedding, name = "The Unnamed"
   - When cluster reaches archetype_naming_threshold events, Claude generates a name
   - Generated names follow "The [Noun]" or "[Noun-phrase]" pattern in ancestral register
   - Centroid list is refreshed after new cluster creation within a batch
   - `archetype_naming_threshold` is configurable via environment variable
   - Re-seeded data shows The Table no longer at 68% of events

6. **DEF-021 truncation fix:**
   - Identified the source of the 10,243-char limit
   - Fix applied — segments are no longer truncated mid-sentence
   - Re-seeded data: previously truncated segments now have full content

### Performance Benchmarks

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| Segmentation API call | < 60s per transcript | Timed during re-seed |
| Significance filtering | < 1ms per segment | In-memory threshold comparison |
| Archetype naming | < 10s per naming call | Timed during re-seed |

### Config Changes

| Env Var | Pydantic Model | Field Name | Type | Default |
|---------|---------------|------------|------|---------|
| `SIGNIFICANCE_THRESHOLD` | `Settings` | `significance_threshold` | float | 0.3 |
| `ARCHETYPE_NAMING_THRESHOLD` | `Settings` | `archetype_naming_threshold` | int | 3 |

## Dependencies
- Sprint 3.5 complete (current state: 166 tests, 48 events across 6 clusters)
- Migration SQL must be run in Supabase SQL editor before pipeline integration sessions (S4/S5)
- Anthropic API available for significance scoring and archetype naming
- OpenAI API available for embedding new events

## Relevant Decisions
- DEC-011: Seed clusters + new clusters when below threshold — designed but creation path never built. This sprint implements it.
- DEC-018: Thematic segmentation for batch and live Granola pipelines — foundation for significance scoring.
- DEC-019: Combined segmentation + label in single Claude call — Sprint 4 extends this JSON schema with significance.
- DEC-020: Boundary-based segmentation output — provides start_line/end_line for raw_input FK.

## Relevant Risks
- RSK-002 (High): Myth generation fable risk — label quality directly affects how constellations read. Marginalia register for labels is a mitigation.
- RSK-007 (Medium): Philosophical coherence under implementation pressure — significance filtering is a philosophical choice (what counts as meaningful?) that needs care in prompt design.

## Session Count Estimate
6 sessions estimated. Two foundation sessions (segmentation core, DB schema) can proceed independently. One self-contained module (archetype creation). Two pipeline integration sessions (Granola, Telegram). One investigation + re-seed session.
