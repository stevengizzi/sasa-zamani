# Sprint 2: Doc Update Checklist

## After Sprint Completion

### docs/project-knowledge.md
- [ ] Update "Current State" section: active sprint → none, tests count, sprints completed
- [ ] Update "Next sprint" to Sprint 3
- [ ] Add new DEC entries to Key Active Decisions table
- [ ] Note myth endpoint is now functional (not stub)

### docs/architecture.md
- [ ] Document xs computation flow (cluster assignment → compute_xs → store in events table)
- [ ] Document myth generation flow (frontend → /myth → myth.py → Claude API → myths table cache)
- [ ] Update API Endpoints table: `/myth` POST description (currently listed but stub)
- [ ] Update EventResponse fields: add xs, day
- [ ] Update ClusterResponse fields: add glyph_id, myth_text, is_seed
- [ ] Add MythRequest/MythResponse to API documentation
- [ ] Update Frontend description: "Fetches event data from backend REST API on load" (remove "periodically")
- [ ] Update Tech Stack table: add Anthropic SDK

### docs/decision-log.md
- [ ] New DEC: xs computed server-side during cluster assignment (cluster-center + offset for Sprint 2, embedding-derived for Sprint 4)
- [ ] New DEC: Edge computation strategy (cluster co-membership Sprint 2, embedding similarity Sprint 3)
- [ ] New DEC: Frontend edge array generic structure (forward-compatible data swap)
- [ ] Assign DEC numbers from reserved range

### docs/dec-index.md
- [ ] Add new DEC entries to quick-reference index

### docs/sprint-history.md
- [ ] Add Sprint 2 entry: name, session count, test delta, key outcomes, carry-forwards, review verdicts

### docs/risk-register.md
- [ ] RSK-002 (myth fable risk): update status based on myth generation testing results
- [ ] RSK-004 (frontend scope creep): update status — did the migration stay in scope?
- [ ] RSK-007 (philosophical coherence): update based on myth quality and copy tone in UI

### docs/roadmap.md
- [ ] Update Sprint 2 status to complete with summary
- [ ] Confirm Sprint 3 scope includes `/edges` endpoint
- [ ] Add any new DEF items discovered during sprint

### CLAUDE.md
- [ ] Update session context for Sprint 3 readiness
- [ ] Note completed myth endpoint, frontend migration
- [ ] Update test count
