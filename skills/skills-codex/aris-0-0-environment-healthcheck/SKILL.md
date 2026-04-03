---
name: aris-0-0-environment-healthcheck
description: "Run a front-loaded environment and dependency preflight for the ARIS pipeline. Checks reviewer backends, experiment runtime, LaTeX toolchain, and required input artifacts before expensive stages begin."
argument-hint: [workflow-stage-or-context]
allowed-tools: Bash(*), Read, Grep, Glob, Write, Edit
---

# Environment Healthcheck

Run a front-loaded environment and dependency preflight for: **$ARGUMENTS**

## Output

Write the canonical preflight report to:
- `00_ENVIRONMENT_HEALTHCHECK.md`

Use this header:

```md
> Artifact: 00_ENVIRONMENT_HEALTHCHECK.md
> Skill: aris-0-0-environment-healthcheck
> Stage: 00 Environment Healthcheck
> Inputs: user request, CLAUDE.md, local toolchain state
> Outputs: 00_ENVIRONMENT_HEALTHCHECK.md
> Status: completed | blocked
> Generated: [today]
```

## Workflow

### Step 1: Detect requested stage

Infer which workflow is about to run:
- full pipeline
- experiment bridge / run
- paper writing / compile
- custom stage from `$ARGUMENTS`

### Step 2: Read local project context

Check for:
- `CLAUDE.md`
- `00_ENVIRONMENT_HEALTHCHECK.md` (reuse if still current, otherwise overwrite)
- canonical stage artifacts when relevant:
  - `01_IDEA_REPORT.md`
  - `02_EXPERIMENT_PLAN.md`
  - `03_CLAIMS_FROM_RESULTS.md`
  - `04_NARRATIVE_REPORT.md`
  - `05_PAPER_PLAN.md`
- legacy fallback artifacts when canonical files do not exist

### Step 3: Check core dependencies

Always verify:
- Python available
- reviewer backend availability if the stage references external review:
  - Codex MCP / configured reviewer path
- shell tools used by downstream skills

When the stage includes experiment execution, verify:
- local / remote / vast.ai environment is specified in `CLAUDE.md` or inferable
- `ssh` available when remote workflows are expected
- `vastai` available when `gpu: vast`
- W&B availability only if requested by project config

When the stage includes paper writing, verify:
- `pdflatex`
- `latexmk`
- `bibtex`
- `pdfinfo`
- `pdffonts`
- `pdftotext`
- matplotlib / plotting stack if auto figures are expected

### Step 4: Check required inputs

For each stage, verify required artifacts exist.

Recommended canonical flow:
- full pipeline start: no required upstream artifact
- experiment bridge: `02_EXPERIMENT_PLAN.md` preferred, fallback to legacy experiment plan
- auto review: `02_EXPERIMENT_RESULTS.md` or `EXPERIMENT_LOG.md` / tracker / logs
- paper writing: `04_NARRATIVE_REPORT.md` preferred, fallback to legacy narrative report
- submission gate: `paper/main.pdf`, `05_PAPER_PLAN.md`, `03_CLAIMS_FROM_RESULTS.md`

### Step 5: Check skill availability

Build a stage-aware required skill set and verify each required skill is available.

Canonical required sets:
- full pipeline:
  - `aris-0-0-environment-healthcheck`
  - `aris-0-2-idea-discovery`
  - `aris-0-3-experiment-bridge`
  - `aris-3-1-auto-review-loop`
  - `aris-4-7-paper-writing`
  - `aris-4-8-submission-gate`
- idea discovery:
  - `aris-1-1-research-lit`
  - `aris-1-4-idea-creator`
  - `aris-1-5-novelty-check`
  - `aris-1-6-research-review`
  - `aris-1-9-research-refine-pipeline`
- experiment bridge:
  - `aris-2-1-run-experiment`
  - `aris-2-2-monitor-experiment`
- paper writing:
  - `aris-4-1-paper-plan`
  - `aris-4-2-paper-figure`
  - `aris-4-4-paper-write`
  - `aris-4-5-paper-compile`
  - `aris-4-6-auto-paper-improvement-loop`

For each required skill, verify:
- directory exists under active skill pack (`skills/` at minimum; `skills/skills-codex/` when Codex pack is being used)
- `SKILL.md` exists
- frontmatter `name` matches expected canonical name
- name prefix is valid: `aris-` or `aris-common-`

Status policy:
- missing required skill => `FAIL` and mark report status as `blocked`
- optional reviewer overlay pack missing => `WARN`

### Step 6: Write the health report

```md
# [00] Environment Healthcheck

> Artifact: 00_ENVIRONMENT_HEALTHCHECK.md
> Skill: aris-0-0-environment-healthcheck
> Stage: 00 Environment Healthcheck
> Inputs: [detected context]
> Outputs: 00_ENVIRONMENT_HEALTHCHECK.md
> Status: completed | blocked
> Generated: [today]

## Requested Stage
- [stage]

## Dependency Status
| Check | Status | Notes |
|------|--------|-------|
| Python | PASS/FAIL | ... |
| Reviewer backend | PASS/FAIL | ... |
| Experiment runtime | PASS/FAIL | ... |
| LaTeX toolchain | PASS/FAIL | ... |
| Plotting stack | PASS/FAIL | ... |

## Artifact Status
| Artifact | Status | Notes |
|---------|--------|-------|
| 02_EXPERIMENT_PLAN.md | PASS/FAIL | ... |
| 04_NARRATIVE_REPORT.md | PASS/FAIL | ... |

## Skill Availability
| Skill | Required By Stage | Pack | Status | Notes |
|------|--------------------|------|--------|-------|
| aris-0-2-idea-discovery | full pipeline | skills | PASS/WARN/FAIL | ... |
| aris-3-1-auto-review-loop | full pipeline | skills-codex (if used) | PASS/WARN/FAIL | ... |
| aris-4-7-paper-writing | paper writing | skills | PASS/WARN/FAIL | ... |

## Blocking Issues
- [issue list]

## Ready For
- [next skill or stage]
```

## Rules

- Prefer canonical prefixed artifacts; fallback to legacy names only when needed.
- Fail early on missing hard dependencies instead of letting expensive stages start.
- Distinguish **blocked** vs **warning** clearly.
- Overwrite `00_ENVIRONMENT_HEALTHCHECK.md` with the latest check; this file is a status snapshot.
