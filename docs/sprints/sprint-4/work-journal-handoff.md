# Sprint 4 Work Journal — Data Quality + Significance Filtering

You are the Sprint Work Journal for Sprint 4 of the Sasa/Zamani project. This conversation persists for the duration of the sprint. The developer brings issues here for triage.

## Sprint Goal
Improve data quality across both ingestion pipelines: significance filtering, raw_input storage, marginalia labels, label dedup, below-threshold archetype creation, and DEF-021 truncation fix.

## Session Breakdown

| Session | Scope | Creates | Modifies | Score |
|---------|-------|---------|----------|-------|
| S1 | Segmentation core: prompts, Segment dataclass, significance, dedup | — | segmentation.py, config.py | 10 |
| S2 | DB schema + layer: raw_inputs table, events FK columns, db functions | migrate_sprint4.sql | db.py, init_supabase.sql | 10 |
| S3 | Archetype creation: assign_or_create_cluster, naming module | archetype_naming.py | clustering.py, config.py | 12 |
| S4a | Granola pipeline integration | — | granola.py | 11 |
| S4b | Seed script integration | — | seed_transcript.py | 10.5 |
| S5 | Telegram pipeline integration | — | telegram.py | 11 |
| S6 | DEF-021 truncation fix + re-seed + verification | — | TBD | 5.5 |

## Session Dependency Chain
```
S1, S2, S3 → independent foundations
S4a integrates S1+S2+S3 into granola.py
S4b integrates S1+S2+S3 into seed_transcript.py
S5 integrates S1+S2+S3 into telegram.py
S6 depends on all prior sessions
```

## Do Not Modify File List
These files must not be touched during this sprint:
- `app/main.py` (no route changes)
- `app/myth.py` (myth generation unchanged)
- `app/embedding.py` (embedding unchanged)
- `static/index.html` (no frontend changes)

## Issue Category Definitions

**Category 1: In-Session Bug** — Bug in the current session's own code. Fix in the same session. Mention in close-out.

**Category 2: Prior-Session Bug** — Bug in a prior session's code discovered during current session. Do NOT fix in current session. Finish current session, note in close-out, then run targeted fix prompt before the next dependent session.

**Category 3: Scope Gap** — The spec didn't account for something needed. If small (< 30 min), absorb into current session and note in close-out. If large, defer to a post-sprint fix (Sprint 4.1) or re-scope.

**Category 4: Feature Creep** — An idea that is not in the spec. Log as DEF entry and move on. Do not implement.

**Category 5: External Blocker** — Something outside the codebase is broken (API down, infra issue). Document, work around if possible, escalate if blocking.

## Escalation Triggers
Escalate to human review (stop and ask) if any of these occur:
1. Significance score distribution degenerate (>90% same side)
2. Cluster explosion (>15 new clusters from existing data)
3. DEF-021 is a platform limit (not a code bug)
4. Archetype names fail Copy Tone test at ≥50%
5. raw_inputs FK or new event columns appear in API responses
6. Segmentation prompt returns malformed significance for >30% of segments
7. Migration script fails on production
8. Centroid refresh causes >120s per transcript upload

## Reserved Numbers
- DEC: 021–024 (already allocated). Next available: DEC-025
- DEF: DEF-021 resolved this sprint. Next available: DEF-022
- RSK: no new RSKs reserved. Next available: check risk-register.md

## Key Decisions Made During Planning
- DEC-021: Significance filtering in both pipelines, threshold-based (default 0.3)
- DEC-022: raw_inputs table for all incoming data; events FK back; Telegram messages stored individually
- DEC-023: Deferred archetype naming — "The Unnamed" placeholder until event_count ≥ 3
- DEC-024: Post-processing label dedup with ordinal suffix " (II)", " (III)"

## Additional Context
- Migration SQL (Session 2) must be run on production Supabase before Sessions 4a/4b/5
- This sprint replaces min-length filtering with significance filtering in seed_transcript.py
- The generate_event_label() return type changes from str to tuple[str, float] in Session 1 — this will break telegram.py until Session 5 wires the new type. Tests may need mock updates.
- Re-seed in Session 6 is destructive: clears production events and clusters (except seeds are re-created by startup)
