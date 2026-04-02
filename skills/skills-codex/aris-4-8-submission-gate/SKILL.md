---
name: aris-4-8-submission-gate
description: "Verify whether a generated paper package is actually submission-ready. Checks PDF existence, page limits, unresolved markers, manual figure completion, claim-evidence coverage, and venue-facing submission blockers."
argument-hint: [paper-directory-or-pdf]
allowed-tools: Bash(*), Read, Grep, Glob, Write, Edit
---

# Submission Gate

Verify whether the paper package is truly submission-ready for: **$ARGUMENTS**

## Output

Write the final verification report to:
- `06_SUBMISSION_GATE.md`

Use this header:

```md
> Artifact: 06_SUBMISSION_GATE.md
> Skill: aris-4-8-submission-gate
> Stage: 06 Submission Gate
> Inputs: paper/main.pdf, 05_PAPER_PLAN.md, 03_CLAIMS_FROM_RESULTS.md, figure manifest
> Outputs: 06_SUBMISSION_GATE.md
> Status: READY | READY_WITH_WARNINGS | BLOCKED
> Generated: [today]
```

## Required Inputs

Prefer canonical files:
- `paper/main.pdf`
- `05_PAPER_PLAN.md`
- `03_CLAIMS_FROM_RESULTS.md`
- `05_FIGURE_MANIFEST.md` if present

Fallback to legacy files only when canonical ones are absent:
- `PAPER_PLAN.md` (fallback for `05_PAPER_PLAN.md`)
- `CLAIMS_FROM_RESULTS.md` (fallback for `03_CLAIMS_FROM_RESULTS.md`)
- figure plan sections in paper plan / figure outputs

## Workflow

### Step 1: Verify package exists

Check:
- PDF exists and is non-empty
- main paper sources exist
- compile log exists if available

### Step 2: Run hard submission checks

Check for blockers:
- page limit violation
- unresolved citations / undefined references
- `[VERIFY]`, `TODO`, `FIXME`, `XXX`
- missing required manual figures
- anonymous submission violations when applicable
- font embedding failures
- missing claim-evidence coverage for intro claims

### Step 3: Determine manual figure status

If a figure manifest exists, inspect all entries.

Treat any HIGH-priority figure with:
- `manual-required`
- `manual-placeholder`
- `missing`

as a submission blocker unless the paper plan explicitly marks it as optional appendix-only.

### Step 4: Decide verdict

Return one of:
- `READY` — no blocking issues
- `READY_WITH_WARNINGS` — minor issues remain but package is still plausibly submittable
- `BLOCKED` — submission should not proceed

### Step 5: Write the report

```md
# [06] Submission Gate Report

> Artifact: 06_SUBMISSION_GATE.md
> Skill: aris-4-8-submission-gate
> Stage: 06 Submission Gate
> Inputs: paper/main.pdf, 05_PAPER_PLAN.md, 03_CLAIMS_FROM_RESULTS.md, figure manifest
> Outputs: 06_SUBMISSION_GATE.md
> Status: READY | READY_WITH_WARNINGS | BLOCKED
> Generated: [today]

## Verdict
- Status: READY | READY_WITH_WARNINGS | BLOCKED
- Venue: [venue]
- PDF: `paper/main.pdf`

## Hard Checks
| Check | Status | Notes |
|------|--------|-------|
| PDF exists | PASS/FAIL | ... |
| Page limit | PASS/FAIL | ... |
| Undefined refs/citations | PASS/FAIL | ... |
| VERIFY/TODO markers | PASS/FAIL | ... |
| Manual figures complete | PASS/FAIL | ... |
| Anonymity | PASS/FAIL | ... |
| Font embedding | PASS/FAIL | ... |
| Claim-evidence coverage | PASS/FAIL | ... |

## Blocking Issues
- [issues]

## Warnings
- [warnings]

## Next Action
- [submit / fix issues / regenerate figures / revise claims]
```

## Rules

- This skill is a verifier, not a broad auto-fix loop.
- Prefer canonical prefixed artifacts; fallback to legacy names only when necessary.
- A compiled PDF alone is not enough for `READY`.
- Missing high-priority manual figures should default to `BLOCKED`.
