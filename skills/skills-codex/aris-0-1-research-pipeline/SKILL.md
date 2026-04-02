---
name: aris-0-1-research-pipeline
description: "Full research pipeline: Workflow 1 (idea discovery) → implementation → Workflow 2 (auto review loop). Goes from a broad research direction all the way to a submission-ready paper. Use when user says \"全流程\", \"full pipeline\", \"从找idea到投稿\", \"end-to-end research\", or wants the complete autonomous research lifecycle."
argument-hint: [research-direction]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Agent, Skill, mcp__codex__codex, mcp__codex__codex-reply
---

# Full Research Pipeline: Idea → Paper → Submission Gate

End-to-end autonomous research workflow for: **$ARGUMENTS**

## Canonical Artifacts

Prefer these staged markdown artifacts throughout the pipeline:
- `00_ENVIRONMENT_HEALTHCHECK.md`
- `01_IDEA_REPORT.md`
- `01_FINAL_PROPOSAL.md`
- `02_EXPERIMENT_PLAN.md`
- `02_EXPERIMENT_TRACKER.md`
- `02_EXPERIMENT_RESULTS.md`
- `03_AUTO_REVIEW.md`
- `03_CLAIMS_FROM_RESULTS.md`
- `04_NARRATIVE_REPORT.md`
- `05_PAPER_PLAN.md`
- `06_SUBMISSION_GATE.md`

Fallback to legacy names only when the canonical prefixed file is absent.

## Constants

- **AUTO_PROCEED = true** — When `true`, Gate 1 auto-selects the top-ranked idea (highest pilot signal + novelty confirmed) and continues to implementation. When `false`, always waits for explicit user confirmation before proceeding.
- **ARXIV_DOWNLOAD = false** — When `true`, `/aris-1-1-research-lit` downloads the top relevant arXiv PDFs during literature survey. When `false` (default), only fetches metadata via arXiv API. Passed through to `/aris-0-2-idea-discovery` → `/aris-1-1-research-lit`.
- **HUMAN_CHECKPOINT = false** — When `true`, the auto-review loops (Stage 4) pause after each round's review to let you see the score and provide custom modification instructions before fixes are implemented. When `false` (default), loops run fully autonomously. Passed through to `/aris-3-1-auto-review-loop`.

> 💡 Override via argument, e.g., `/aris-0-1-research-pipeline "topic" — AUTO_PROCEED: false, human checkpoint: true`.

## Overview

This skill chains the entire research lifecycle into a single pipeline:

```
/aris-0-0-environment-healthcheck → /aris-0-2-idea-discovery → /aris-0-3-experiment-bridge → /aris-3-1-auto-review-loop → /aris-4-7-paper-writing → /aris-4-8-submission-gate
       preflight                   Workflow 1                  Workflow 1.5                Workflow 2                 Workflow 3                 final gate
```

It orchestrates the full path from idea selection to final PDF verification.

## Pipeline

### Stage 0: Environment Healthcheck

Before any expensive work, run:

```
/aris-0-0-environment-healthcheck "full pipeline: $ARGUMENTS"
```

**Output:** `00_ENVIRONMENT_HEALTHCHECK.md`

If the report contains blocking issues (missing reviewer backend, unavailable experiment runtime, missing LaTeX toolchain for paper stages), stop early and ask the user to fix them before continuing.

### Stage 1: Idea Discovery (Workflow 1)

If `RESEARCH_BRIEF.md` exists in the project root, it will be automatically loaded as detailed context (replaces one-line prompt). See `templates/RESEARCH_BRIEF_TEMPLATE.md`.

Invoke the idea discovery pipeline:

```
/aris-0-2-idea-discovery "$ARGUMENTS"
```

This internally runs: `/aris-1-1-research-lit` → `/aris-1-4-idea-creator` → `/aris-1-5-novelty-check` → `/aris-1-6-research-review`

**Output:** `01_IDEA_REPORT.md` with ranked, validated, pilot-tested ideas (fallback readers may still consume `IDEA_REPORT.md` when the canonical file is absent).

**🚦 Gate 1 — Human Checkpoint:**

After `01_IDEA_REPORT.md` is generated, **pause and present the top ideas to the user**:

```
📋 Idea Discovery complete. Top ideas:

1. [Idea 1 title] — Pilot: POSITIVE (+X%), Novelty: CONFIRMED
2. [Idea 2 title] — Pilot: WEAK POSITIVE (+Y%), Novelty: CONFIRMED
3. [Idea 3 title] — Pilot: NEGATIVE, eliminated

Recommended: Idea 1. Shall I proceed with implementation?
```

**If AUTO_PROCEED=false:** Wait for user confirmation before continuing. The user may:
- **Approve an idea** → proceed to Stage 2.
- **Pick a different idea** → proceed with their choice.
- **Request changes** (e.g., "combine Idea 1 and 3", "focus more on X") → update the idea prompt with user feedback, re-run `/aris-0-2-idea-discovery` with refined constraints, and present again.
- **Reject all ideas** → collect feedback on what's missing, re-run Stage 1 with adjusted research direction. Repeat until the user commits to an idea.
- **Stop here** → save current state to `01_IDEA_REPORT.md` for future reference.

**If AUTO_PROCEED=true:** Present the top ideas, wait 10 seconds for user input. If no response, auto-select the #1 ranked idea (highest pilot signal + novelty confirmed) and proceed to Stage 2. Log: `"AUTO_PROCEED: selected Idea 1 — [title]"`.

> ⚠️ **This gate waits for user confirmation when AUTO_PROCEED=false.** When `true`, it auto-selects the top idea after presenting results. The rest of the pipeline (Stages 2-4) is expensive (GPU time + multiple review rounds), so set `AUTO_PROCEED=false` if you want to manually choose which idea to pursue.

### Stage 2: Experiment Bridge (Workflow 1.5)

Once the user confirms which idea to pursue, hand off to the implementation-and-results bridge:

```
/aris-0-3-experiment-bridge "02_EXPERIMENT_PLAN.md"
```

Prefer canonical artifacts:
- `02_EXPERIMENT_PLAN.md`
- `02_EXPERIMENT_TRACKER.md`
- `01_FINAL_PROPOSAL.md`

Fallback to legacy files only if the canonical versions do not exist.

**Expected outputs:**
- `02_EXPERIMENT_RESULTS.md`
- updated `02_EXPERIMENT_TRACKER.md`
- optional `EXPERIMENT_LOG.md`

### Stage 3: Auto Review Loop (Workflow 2)

Once initial results are in, start the autonomous improvement loop:

```
/aris-3-1-auto-review-loop "$ARGUMENTS — [chosen idea title]"
```

**What this does (up to 4 rounds):**
1. GPT-5.4 xhigh reviews the work (score, weaknesses, minimum fixes)
2. Claude Code implements fixes (code changes, new experiments, reframing)
3. Deploy fixes, collect new results
4. Re-review → repeat until score ≥ 6/10 or 4 rounds reached

**Output:** `03_AUTO_REVIEW.md` with full review history and final assessment.

### Stage 5: Final Summary

After the auto-review loop completes, write a final status report:

```markdown
# Research Pipeline Report

**Direction**: $ARGUMENTS
**Chosen Idea**: [title]
**Date**: [start] → [end]
**Pipeline**: idea-discovery → implement → run-experiment → auto-review-loop

## Journey Summary
- Ideas generated: X → filtered to Y → piloted Z → chose 1
- Implementation: [brief description of what was built]
- Experiments: [number of GPU experiments, total compute time]
- Review rounds: N/4, final score: X/10

## Final Status
- [ ] Ready for submission / [ ] Needs manual follow-up

## Remaining TODOs (if any)
- [items flagged by reviewer that weren't addressed]

## Files Changed
- [list of key files created/modified]
```

## Key Rules

- **Large file handling**: If the Write tool fails due to file size, immediately retry using Bash (`cat << 'EOF' > file`) to write in chunks. Do NOT ask the user for permission — just do it silently.

- **Human checkpoint after Stage 1 is controlled by AUTO_PROCEED.** When `false`, do not proceed without user confirmation. When `true`, auto-select the top idea after presenting results.
- **Stages 2-4 can run autonomously** once the user confirms the idea. This is the "sleep and wake up to results" part.
- **If Stage 4 ends at round 4 without positive assessment**, stop and report remaining issues. Do not loop forever.
- **Budget awareness**: Track total GPU-hours across the pipeline. Flag if approaching user-defined limits.
- **Documentation**: Every stage updates its own output file. The full history should be self-contained.
- **Fail gracefully**: If any stage fails (no good ideas, experiments crash, review loop stuck), report clearly and suggest alternatives rather than forcing forward.

## Typical Timeline

| Stage | Duration | Can sleep? |
|-------|----------|------------|
| 1. Idea Discovery | 30-60 min | Yes if AUTO_PROCEED=true |
| 2. Implementation | 15-60 min | Yes (autonomous after Gate 1) |
| 3. Deploy | 5 min + experiment time | Yes ✅ |
| 4. Auto Review | 1-4 hours (depends on experiments) | Yes ✅ |

**Sweet spot**: Run Stage 1-2 in the evening, launch Stage 3-4 before bed, wake up to a reviewed paper.
