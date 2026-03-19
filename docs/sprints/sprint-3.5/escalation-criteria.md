# Sprint 3.5 — Escalation Criteria

Escalate to a Tier 3 review conversation if:

1. **Segmentation output ratio anomaly:** Thematic segmentation produces < 50% or > 150% of the speaker-turn segment count for either transcript. This suggests the segmentation prompt is either too aggressive (merging everything) or too granular (not actually grouping thematically).

2. **Claude API cost per transcript exceeds $0.50:** Indicates the prompt is too large or producing excessive output. Review the segmentation prompt design before proceeding with production seeding.

3. **Segmentation produces semantically incoherent segments on manual review:** If the developer reads 5+ segments and finds they don't hold together thematically, the prompt needs rework before pipeline integration.

4. **Test pass count drops below 118:** Indicates a regression introduced by the sprint changes.

5. **`insert_event()` backward compatibility broken:** If any existing caller fails after adding the `participants` parameter. This should not happen (default None), but if it does, it's a schema design issue.

6. **Schema change requires migration beyond single ALTER TABLE:** If the `participants` column addition reveals the need for data migration, foreign keys, or index changes beyond the simple column add.

Escalate to the Work Journal if (during any session):
- A file not in the session's "Modifies" list needs changes
- A file not in the session's "Creates" list is needed
- Test count exceeds estimate by > 50%
- Claude API behaves unexpectedly (rate limits, response format changes)
- Segmentation output structure doesn't match the expected `Segment` dataclass
