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
- `paper/PAPER_IMPROVEMENT_LOG.md` if present
- `paper/PAPER_ISSUE_LEDGER.md` if present
- `figures/FIGURE_ISSUE_LEDGER.md` if present
- `figures/FIGURE_QUALITY_REPORT.md` if present
- `05_FIGURE_MANIFEST.md` if present
- `07_REPRODUCIBILITY_AND_AUTHENTICITY.md` if present (preferred for evidence audit)

Fallback to legacy files only when canonical ones are absent:
- `PAPER_PLAN.md` (fallback for `05_PAPER_PLAN.md`)
- `CLAIMS_FROM_RESULTS.md` (fallback for `03_CLAIMS_FROM_RESULTS.md`)
- figure plan sections in paper plan / figure outputs

## Constants

- **MIN_FINAL_SCORE = 8.0** — Minimum acceptable final paper quality score from the improvement loop.

## Workflow

### Step 1: Verify package exists

Check:
- PDF exists and is non-empty
- main paper sources exist
- compile log exists if available

### Step 2: Run hard submission checks

Check for blockers:
- `[VERIFY]`, `TODO`, `FIXME`, `XXX` that signal unresolved scientific/content uncertainty
- missing required manual figures
- missing claim-evidence coverage for intro claims
- unresolved CRITICAL issues in `paper/PAPER_ISSUE_LEDGER.md` if present
- unresolved CRITICAL figure issues in `figures/FIGURE_ISSUE_LEDGER.md` if present
- strongest safe claim inconsistent across abstract / introduction / conclusion
- missing documented closure for major paper-quality issues
- final improvement score below `MIN_FINAL_SCORE`
- unresolved `CRITICAL` or `MAJOR` issues in `paper/PAPER_ISSUE_LEDGER.md` if present
- strongest safe claim inconsistent between paper text and claims artifacts (`03_CLAIMS_FROM_RESULTS.md` / fallback `CLAIMS_FROM_RESULTS.md`)
- reproducibility evidence missing or insufficient (e.g., no runnable setup/training/eval instructions, no config/hyperparameter provenance, no clear checkpoint/data reference)
- missing or incomplete standalone evidence artifact `07_REPRODUCIBILITY_AND_AUTHENTICITY.md` (or equivalent fields from the same template)
- content judged thin/shallow relative to venue bar (insufficient analysis depth, weak ablation/controls, or under-justified conclusions)
- unresolved high-impact review findings from the latest paper improvement loop (quality issues not closed)

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

For loop/judge compatibility, also emit:
- `blocking_issues`: normalized blocker list
- `next_action`: `submit` | `fix_and_rerun_improvement_loop` | `regenerate_figures` | `revise_claims`
- `stop_reason`: concise reason code when `BLOCKED` (e.g., `score_below_threshold`, `ledger_unresolved_major`)
- `status`: mirror of verdict for downstream automation (`ready`, `ready_with_warnings`, `blocked`)

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
| VERIFY/TODO markers (scientific uncertainty) | PASS/FAIL | ... |
| Manual figures complete | PASS/FAIL | ... |
| Claim-evidence coverage | PASS/FAIL | ... |
| Final score >= MIN_FINAL_SCORE | PASS/FAIL | ... |
| No unresolved CRITICAL/MAJOR issues in ledger | PASS/FAIL | ... |
| Strongest safe claim consistency (paper vs claims artifacts) | PASS/FAIL | ... |
| Reproducibility evidence completeness | PASS/FAIL | setup/config/checkpoint/data provenance |
| High-impact review issues closed | PASS/FAIL | from latest improvement loop/ledger |

## Content Quality Gate
| Check | Status | Notes |
|------|--------|-------|
| Major issue closure documented | PASS/FAIL | ... |
| No unresolved CRITICAL issue in ledger | PASS/FAIL | ... |
| No unresolved CRITICAL figure issue | PASS/FAIL | ... |
| Strongest safe claim consistent | PASS/FAIL | ... |
| Claim-evidence coverage preserved after revisions | PASS/FAIL | ... |
| Content depth sufficient for venue bar | PASS/FAIL | analysis/ablation/controls depth |

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
- `READY_WITH_WARNINGS` is only allowed when remaining issues are minor and do not invalidate core claims.
- If final score is below `MIN_FINAL_SCORE`, or unresolved `CRITICAL`/`MAJOR` issues remain, verdict must be `BLOCKED`.
- If strongest safe claim is inconsistent across abstract/introduction/conclusion or claims artifacts, verdict must be `BLOCKED`.
- If reproducibility evidence is missing/incomplete, verdict must be `BLOCKED`.
- If content depth is below venue bar (thin analysis/ablations/controls), verdict must be `BLOCKED`.
- This gate prioritizes scientific quality and evidence closure; formatting workflow items (anonymity, line numbering, submission portal fields) are out of scope.
