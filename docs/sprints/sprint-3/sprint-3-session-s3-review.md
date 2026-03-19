# Tier 2 Review: Sprint 3, Session S3

## Instructions
You are conducting a Tier 2 code review. This is a READ-ONLY session.
Do NOT modify any source code files.

Follow the review skill in .claude/skills/review.md.

Your review report MUST include a structured JSON verdict at the end,
fenced with ```json:structured-verdict.

**Write the review report to a file:**
docs/sprints/sprint-3/session-s3-review.md

## Review Context
Read the following file for the Sprint Spec, Specification by Contradiction,
Sprint-Level Regression Checklist, and Sprint-Level Escalation Criteria:

`docs/sprints/sprint-3/review-context.md`

## Tier 1 Close-Out Report
Read the close-out report from:
`docs/sprints/sprint-3/session-s3-closeout.md`

## Review Scope
- Diff to review: `git diff HEAD~1`
- Test command (scoped): `python -m pytest tests/test_myth.py -x -q`
- Files that should NOT have been modified: `app/db.py`, `app/clustering.py`, `app/telegram.py`, `app/granola.py`, `app/config.py`, `app/models.py`, `app/embedding.py`, `app/main.py`, `static/index.html`

## Session-Specific Review Focus
1. Verify only `build_myth_prompt` was changed — `should_regenerate`, `generate_myth`, `get_or_generate_myth` must be untouched
2. Verify PROHIBITED_WORDS and PREFERRED_WORDS constants are preserved (content may adjust, enforcement pattern must remain)
3. Verify thin-cluster path activates at ≤2 events with distinct prompt variant
4. Verify the prompt includes register guidance from the Design Brief ("ancestral", "marginalia", "scholar")
5. Verify the prompt includes the embarrassment test ("could not have been written without these specific events")
6. Verify function signature is unchanged: `build_myth_prompt(cluster_name: str, event_labels: list[str]) -> str`
7. Assess: does the prompt read like it will produce marginalia-in-an-old-book output, or does it lean toward wellness/therapy?

## Additional Context
This session is prompt engineering only. The myth generation architecture (caching, delta-based regeneration, fallback) is untouched. The `scripts/test_myth_quality.py` is a manual tool for human review, not an automated test — it requires live API keys and connects to production.
