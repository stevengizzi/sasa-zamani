# Sprint 4: Doc Update Checklist

After Sprint 4 is complete, update the following documents:

## docs/project-knowledge.md
- [ ] Add DEC-021 (significance filtering), DEC-022 (raw_inputs table), DEC-023 (deferred archetype naming), DEC-024 (post-processing label dedup)
- [ ] Update "Current State" section: test count, sprint count, event count, cluster count
- [ ] Update "Key Active Decisions" table with DEC-021 through DEC-024
- [ ] Add `significance_threshold` and `archetype_naming_threshold` to config references
- [ ] Update "Seeded data" line with new event/cluster counts post re-seed
- [ ] Mark DEF-021 as resolved
- [ ] Update Max DEC / Max DEF numbers

## docs/architecture.md
- [ ] Add `raw_inputs` table to the database schema diagram
- [ ] Add `raw_input_id`, `start_line`, `end_line` to events table in the schema diagram
- [ ] Add `app/archetype_naming.py` to "Key backend files" list
- [ ] Update pipeline flow description to include significance filtering step
- [ ] Note that clusters can now be dynamic (is_seed=false) with deferred naming

## docs/decision-log.md
- [ ] Add full DEC-021 entry (significance filtering: both pipelines, threshold-based, configurable)
- [ ] Add full DEC-022 entry (raw_inputs table replacing transcripts concept, FK from events)
- [ ] Add full DEC-023 entry (deferred archetype naming, "The Unnamed" placeholder, threshold=3)
- [ ] Add full DEC-024 entry (post-processing label dedup with ordinal suffix)

## docs/dec-index.md
- [ ] Add DEC-021 through DEC-024 to quick-reference index

## docs/roadmap.md
- [ ] Update Sprint 4 entry with "Status: Complete" and delivered items
- [ ] Mark DEF-021 as resolved
- [ ] Add any new DEF items discovered during sprint

## docs/risk-register.md
- [ ] Update RSK-002 (fable risk) if label quality improvements affect the mitigation status
- [ ] Update RSK-007 (philosophical coherence) — significance filtering is a philosophical choice now implemented

## CLAUDE.md
- [ ] Add `significance_threshold` and `archetype_naming_threshold` to config field documentation
- [ ] Add `app/archetype_naming.py` to module list
- [ ] Add `raw_inputs` table to schema documentation
- [ ] Note the `assign_or_create_cluster()` function as the new cluster assignment entry point

## scripts/init_supabase.sql
- [ ] Already updated during Session 2 — verify it matches final production schema
