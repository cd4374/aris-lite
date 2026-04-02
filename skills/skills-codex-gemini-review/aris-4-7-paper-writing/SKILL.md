---
name: "aris-4-7-paper-writing"
description: "Workflow 3: Full paper writing pipeline. Orchestrates paper-plan → paper-figure → paper-write → paper-compile → auto-paper-improvement-loop to go from a narrative report to a polished, submission-ready PDF. Use when user says \"写论文全流程\", \"write paper pipeline\", \"从报告到PDF\", \"paper writing\", or wants the complete paper generation workflow."
---

> Override for Codex users who want **Gemini**, not a second Codex agent, to act as the reviewer. Install this package **after** `skills/skills-codex/*`.

# Workflow 3: Paper Writing Pipeline

Orchestrate a complete paper writing workflow for: **$ARGUMENTS**

## Overview

This skill chains five sub-skills into a single automated pipeline:

```
/aris-4-1-paper-plan → /aris-4-2-paper-figure → /aris-4-4-paper-write → /aris-4-5-paper-compile → /aris-4-6-auto-paper-improvement-loop
  (outline)     (plots)        (LaTeX)        (build PDF)       (review & polish ×2)
```

Each phase builds on the previous one's output. The final deliverable is a polished, reviewed `paper/` directory with LaTeX source and compiled PDF.

In this hybrid pack, the pipeline itself is unchanged, but `aris-4-1-paper-plan` and `aris-4-4-paper-write` use Orchestra-adapted shared references for stronger story framing and prose guidance.

## Constants

- **VENUE = `ICLR`** — Target venue. Options: `ICLR`, `NeurIPS`, `ICML`, `CVPR`, `ACL`, `AAAI`, `ACM`, `IEEE_JOURNAL` (IEEE Transactions / Letters), `IEEE_CONF` (IEEE conferences). Affects style file, page limit, citation format.
- **MAX_IMPROVEMENT_ROUNDS = 2** — Number of review→fix→recompile rounds in the improvement loop.
- **REVIEWER_MODEL = `gemini-review`** — Gemini reviewer invoked through the local `gemini-review` MCP bridge. Set `GEMINI_REVIEW_MODEL` if you need a specific Gemini model override.
- **AUTO_PROCEED = true** — Auto-continue between phases. Set `false` to pause and wait for user approval after each phase.
- **HUMAN_CHECKPOINT = false** — When `true`, the improvement loop (Phase 5) pauses after each round's review to let you see the score and provide custom modification instructions. When `false` (default), the loop runs fully autonomously. Passed through to `/aris-4-6-auto-paper-improvement-loop`.

> Override inline: `/aris-4-7-paper-writing "04_NARRATIVE_REPORT.md" — venue: NeurIPS, human checkpoint: true`
> IEEE example: `/aris-4-7-paper-writing "04_NARRATIVE_REPORT.md" — venue: IEEE_JOURNAL`

## Inputs

This pipeline accepts one of:

1. **`04_NARRATIVE_REPORT.md`** (preferred) or `NARRATIVE_REPORT.md` — structured research narrative with claims, experiments, results, figures
2. **Research direction + experiment results** — the skill will help draft the narrative first
3. **Existing `05_PAPER_PLAN.md`** (preferred) or `PAPER_PLAN.md` — skip Phase 1, start from Phase 2

The more detailed the input (especially figure descriptions and quantitative results), the better the output.

## Pipeline

### Phase 1: Paper Plan

Invoke `/aris-4-1-paper-plan` to create the structural outline:

```
/aris-4-1-paper-plan "$ARGUMENTS"
```

**What this does:**
- Parse `04_NARRATIVE_REPORT.md` first (fallback: `NARRATIVE_REPORT.md`) for claims, evidence, and figure descriptions
- Build a **Claims-Evidence Matrix** — every claim maps to evidence, every experiment supports a claim
- Design section structure (5-8 sections depending on paper type)
- Plan figure/table placement with data sources
- Scaffold citation structure
- GPT-5.4 reviews the plan for completeness

**Output:** `05_PAPER_PLAN.md` with section plan, figure plan, citation scaffolding.

**Checkpoint:** Present the plan summary to the user.

```
📐 Paper plan complete:
- Title: [proposed title]
- Sections: [N] ([list])
- Figures: [N] auto-generated + [M] manual
- Target: [VENUE], [PAGE_LIMIT] pages

Shall I proceed with figure generation?
```

- **User approves** (or AUTO_PROCEED=true) → proceed to Phase 2.
- **User requests changes** → adjust plan and re-present.

### Phase 2: Figure Generation

Invoke `/aris-4-2-paper-figure` to generate data-driven plots and tables:

```
/aris-4-2-paper-figure "05_PAPER_PLAN.md"
```

**What this does:**
- Read figure plan from `05_PAPER_PLAN.md` first (fallback: `PAPER_PLAN.md`)
- Generate matplotlib/seaborn plots from JSON/CSV data
- Generate LaTeX comparison tables
- Create `figures/latex_includes.tex` for easy insertion
- GPT-5.4 reviews figure quality and captions

**Output:** `figures/` directory with PDFs, generation scripts, and LaTeX snippets.

> **Scope:** Auto-generates ~60% of figures (data plots, comparison tables). Architecture diagrams, pipeline figures, and qualitative result grids must be created manually and placed in `figures/` before proceeding. See `/aris-4-2-paper-figure` SKILL.md for details.

**Checkpoint:** List generated vs manual figures.

```
📊 Figures complete:
- Auto-generated: [list]
- Manual (need your input): [list]
- LaTeX snippets: figures/latex_includes.tex

[If manual figures needed]: record placeholders in `05_FIGURE_MANIFEST.md`, add any required manual assets to `figures/`, then proceed when ready.
[If all auto]: Shall I proceed with LaTeX writing?
```

### Phase 3: LaTeX Writing

Invoke `/aris-4-4-paper-write` to generate section-by-section LaTeX:

```
/aris-4-4-paper-write "05_PAPER_PLAN.md"
```

**What this does:**
- Write each section following the plan, with proper LaTeX formatting
- Insert figure/table references from `figures/latex_includes.tex`
- Build `references.bib` from citation scaffolding
- Clean stale files from previous section structures
- Automated bib cleaning (remove uncited entries)
- De-AI polish (remove "delve", "pivotal", "landscape"...)
- GPT-5.4 reviews each section for quality

**Output:** `paper/` directory with `main.tex`, `sections/*.tex`, `references.bib`, `math_commands.tex`.

**Checkpoint:** Report section completion.

```
✍️ LaTeX writing complete:
- Sections: [N] written ([list])
- Citations: [N] unique keys in references.bib
- Stale files cleaned: [list, if any]

Shall I proceed with compilation?
```

### Phase 4: Compilation

Invoke `/aris-4-5-paper-compile` to build the PDF:

```
/aris-4-5-paper-compile "paper/"
```

**What this does:**
- `latexmk -pdf` with automatic multi-pass compilation
- Auto-fix common errors (missing packages, undefined refs, BibTeX syntax)
- Up to 3 compilation attempts
- Post-compilation checks: undefined refs, page count, font embedding
- Precise page verification via `pdftotext`
- Stale file detection

**Output:** `paper/main.pdf`

**Checkpoint:** Report compilation results.

```
🔨 Compilation complete:
- Status: SUCCESS
- Pages: [X] (main body) + [Y] (references) + [Z] (appendix)
- Within page limit: YES/NO
- Undefined references: 0
- Undefined citations: 0

Shall I proceed with the improvement loop?
```

### Phase 5: Auto Improvement Loop

Invoke `/aris-4-6-auto-paper-improvement-loop` to polish the paper:

```
/aris-4-6-auto-paper-improvement-loop "paper/"
```

**What this does (2 rounds):**

**Round 1:** Gemini review reviews the full paper → identifies CRITICAL/MAJOR/MINOR issues → Claude Code implements fixes → recompile → save `main_round1.pdf`

**Round 2:** Gemini review re-reviews with conversation context → identifies remaining issues → Claude Code implements fixes → recompile → save `main_round2.pdf`

**Typical improvements:**
- Fix assumption-model mismatches
- Soften overclaims to match evidence
- Add missing interpretations and notation
- Strengthen limitations section
- Add theory-aligned experiments if needed

**Output:** Three PDFs for comparison + `PAPER_IMPROVEMENT_LOG.md`.

**Format check** (included in improvement loop Step 8): After final recompilation, auto-detect and fix overfull hboxes (content exceeding margins), verify page count vs venue limit, and ensure compact formatting. Any overfull > 10pt is fixed before generating the final PDF.

### Phase 6: Submission Gate

Invoke `/aris-4-8-submission-gate` to verify the package is actually ready to submit:

```
/aris-4-8-submission-gate "paper/"
```

**What this does:**
- Verify `paper/main.pdf` exists and is non-empty
- Check page limits, unresolved refs/citations, TODO/VERIFY markers, anonymity, and font embedding
- Inspect `05_PAPER_PLAN.md`, `03_CLAIMS_FROM_RESULTS.md`, and `05_FIGURE_MANIFEST.md` when present
- Return `READY`, `READY_WITH_WARNINGS`, or `BLOCKED`

**Output:** `06_SUBMISSION_GATE.md`

### Phase 7: Final Report

```markdown
# Paper Writing Pipeline Report

**Input**: [`04_NARRATIVE_REPORT.md` or topic]
**Venue**: [ICLR/NeurIPS/ICML/CVPR/ACL/AAAI/ACM/IEEE_JOURNAL/IEEE_CONF]
**Date**: [today]

## Pipeline Summary

| Phase | Status | Output |
|-------|--------|--------|
| 1. Paper Plan | ✅ | 05_PAPER_PLAN.md |
| 2. Figures | ✅ | figures/ ([N] auto + [M] manual) |
| 3. LaTeX Writing | ✅ | paper/sections/*.tex ([N] sections, [M] citations) |
| 4. Compilation | ✅ | paper/main.pdf ([X] pages) |
| 5. Improvement | ✅ | [score0]/10 → [score2]/10 |
| 6. Submission Gate | ✅ | 06_SUBMISSION_GATE.md |

## Improvement Scores
| Round | Score | Key Changes |
|-------|-------|-------------|
| Round 0 | X/10 | Baseline |
| Round 1 | Y/10 | [summary] |
| Round 2 | Z/10 | [summary] |

## Deliverables
- paper/main.pdf — Final polished paper
- paper/main_round0_original.pdf — Before improvement
- paper/main_round1.pdf — After round 1
- paper/main_round2.pdf — After round 2
- paper/PAPER_IMPROVEMENT_LOG.md — Full review log
- 06_SUBMISSION_GATE.md — Final submission-readiness verdict

## Remaining Issues (if any)
- [items from final review that weren't addressed]

## Next Steps
- [ ] Visual inspection of PDF
- [ ] Resolve any blocking items from `06_SUBMISSION_GATE.md`
- [ ] Add any missing manual figures flagged in `05_FIGURE_MANIFEST.md`
- [ ] Submit to [venue] via OpenReview / CMT / HotCRP
```

## Key Rules

- **Large file handling**: If the Write tool fails due to file size, immediately retry using Bash (`cat << 'EOF' > file`) to write in chunks. Do NOT ask the user for permission — just do it silently.
- **Don't skip phases.** Each phase builds on the previous one — skipping leads to errors.
- **Checkpoint between phases** when AUTO_PROCEED=false. Present results and wait for approval.
- **Manual figures are tracked, not silently ignored.** If the paper needs architecture diagrams or qualitative results, record them in `05_FIGURE_MANIFEST.md`. Paper writing may proceed with placeholders, but `/aris-4-8-submission-gate` should block submission when high-priority manual figures remain incomplete.
- **Compilation must succeed** before entering the improvement loop. Fix all errors first.
- **Preserve all PDFs.** The user needs round0/round1/round2 for comparison.
- **Document everything.** The pipeline report should be self-contained.
- **Respect page limits.** If the paper exceeds the venue limit, suggest specific cuts before the improvement loop.
- **Do not treat a compiled PDF as sufficient.** The pipeline is only truly done after `/aris-4-8-submission-gate` writes `06_SUBMISSION_GATE.md`.

## Composing with Other Workflows

```
/aris-0-2-idea-discovery "direction"         ← Workflow 1: find ideas
implement                           ← write code
/aris-2-1-run-experiment                     ← deploy experiments
/aris-3-1-auto-review-loop "paper topic"     ← Workflow 2: iterate research
/aris-4-7-paper-writing "04_NARRATIVE_REPORT.md"  ← Workflow 3: you are here
                                         submit! 🎉

Or use /aris-0-1-research-pipeline for the full Workflow 0→6 flow,
which now continues through paper writing and `/aris-4-8-submission-gate`.
```

## Typical Timeline

| Phase | Duration | Can sleep? |
|-------|----------|------------|
| 1. Paper Plan | 5-10 min | No |
| 2. Figures | 5-15 min | No |
| 3. LaTeX Writing | 15-30 min | Yes ✅ |
| 4. Compilation | 2-5 min | No |
| 5. Improvement | 15-30 min | Yes ✅ |

**Total: ~45-90 min** for a full paper from narrative report to polished PDF.
