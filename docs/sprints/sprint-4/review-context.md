# Sprint 4: Review Context

> Shared reference for all Tier 2 session reviews.
> Read-only. Follow the review skill in .claude/workflow/claude/skills/review.md.

---

## Sprint Spec

### Goal
Improve data quality across both ingestion pipelines: filter insignificant content, store all raw inputs, redesign labels for a marginalia register, deduplicate labels, implement the designed-but-unbuilt new-cluster creation path (DEC-011), and fix the 10,243-char truncation bug (DEF-021).

### Deliverables
1. **Significance filtering** — Score (0.0–1.0) in segmentation and label prompts. Below `significance_threshold` (default 0.3): stored in raw_inputs, not promoted to events. Both Granola and Telegram pipelines.
2. **Raw input storage** — `raw_inputs` table for all incoming data. Events FK back via `raw_input_id` + `start_line`/`end_line` (nullable). Granola transcripts = full text rows. Telegram messages = one row each.
3. **Better labels** — Marginalia register: proposition, not tag cloud. 4–8 words. "Nakedness as awareness of mortality" not "Garden Eden Fall Naked."
4. **Duplicate label defense** — Intra-transcript uniqueness instruction + post-processing dedup with ordinal suffix.
5. **Below-threshold archetype creation** — New cluster when best similarity < threshold. Placeholder "The Unnamed", deferred naming at event_count ≥ 3. Centroid refresh mid-batch.
6. **DEF-021 truncation fix** — 10,243-char limit identified and fixed.

### Config Changes
| Env Var | Pydantic Field | Type | Default |
|---------|---------------|------|---------|
| `SIGNIFICANCE_THRESHOLD` | `Settings.significance_threshold` | float | 0.3 |
| `ARCHETYPE_NAMING_THRESHOLD` | `Settings.archetype_naming_threshold` | int | 3 |

### Decisions
- DEC-021: Significance filtering, both pipelines, configurable threshold
- DEC-022: raw_inputs table for all incoming data, events FK back
- DEC-023: Deferred archetype naming, "The Unnamed" placeholder, threshold=3
- DEC-024: Post-processing label dedup with ordinal suffix

---

## Specification by Contradiction

### Out of Scope
1. Cross-transcript label uniqueness enforcement
2. Archetype glyphs for dynamic clusters (glyph_id = NULL)
3. Rolling centroid updates
4. Frontend changes — do NOT modify static/index.html
5. Transcript dedup (DEF-018)
6. Label regeneration endpoint/UI
7. Dynamic XS_CENTERS for new clusters (use default 0.50)
8. Significance score storage on event rows
9. Archetype renaming on composition shift

### Do NOT Modify
- `app/main.py`, `app/myth.py`, `app/embedding.py`, `static/index.html`

### Do NOT Change
- `/events` GET response schema (no new fields in response)
- `/clusters` GET response schema
- `/myth` POST behavior
- Seed cluster centroids or is_seed status
- `assign_cluster()` function signature (backward compatibility)

### Edge Cases to Reject (Not Handle)
- Missing significance field → default to 1.0, log warning
- All segments below threshold → empty event list, no error
- Archetype naming API failure → keep "The Unnamed", log error, retry next insertion
- Cluster of one → valid, stays unnamed
- Two similar below-threshold events in batch → second joins first's new cluster via centroid refresh

---

## Sprint-Level Regression Checklist

- [ ] All 166 pre-Sprint 4 tests pass
- [ ] `/events` GET returns valid JSON with existing field schema (no raw_input_id/start_line/end_line)
- [ ] `/clusters` GET returns valid JSON with existing field schema
- [ ] `/myth` POST generates myths for seed clusters
- [ ] Telegram webhook processes text messages end-to-end
- [ ] Granola upload processes transcripts end-to-end
- [ ] event_date, participants, xs populated on new events
- [ ] Seed cluster centroids unchanged
- [ ] compute_xs() works for seed clusters and new clusters
- [ ] increment_event_count() RPC works for seed and dynamic clusters
- [ ] New config fields have defaults (app starts without them)
- [ ] insert_event() backward compatible (callers not passing new fields still work)
- [ ] segment_transcript() returns valid Segments with new fields
- [ ] assign_cluster() still exists unchanged
- [ ] assign_or_create_cluster() returns (cluster_id, similarity, created)
- [ ] Dynamic clusters: is_seed=False, name="The Unnamed", valid centroid
- [ ] maybe_name_cluster() safe on seed clusters (no-op)
- [ ] maybe_name_cluster() safe when below naming threshold (no-op)
- [ ] raw_inputs table accessible
- [ ] ensure_schema() validates raw_inputs
- [ ] dedup_labels and filter_by_significance do not mutate input lists

---

## Sprint-Level Escalation Criteria

1. Significance score distribution degenerate (>90% same side) → pause, redesign prompt
2. Cluster explosion (>15 new clusters from existing data) → pause, tune threshold
3. DEF-021 is a platform limit (not a code bug) → escalate for architectural decision
4. Archetype names fail Copy Tone test at ≥50% → escalate for prompt redesign
5. raw_inputs FK or new event columns appear in API responses → escalate immediately
6. Segmentation prompt returns malformed significance for >30% of segments → redesign prompt
7. Migration script fails on production → do not manually fix, escalate with error
8. Centroid refresh causes >120s per transcript upload → consider batching
