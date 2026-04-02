# Project Files Guide

[中文版](PROJECT_FILES_GUIDE_CN.md) | English

> How to organize project-level state files for ARIS research workflows — what each file does, when to write it, and how they relate to each other.

## The Problem

ARIS workflows generate a lot of information across multiple stages: ideas, experiment plans, results, review feedback, decisions. Without clear file conventions, this information gets scattered across chat sessions and lost on context compaction or new sessions.

This guide establishes a layered file system where each file has a clear purpose, update trigger, and relationship to other files.

## File Overview

```
project/
├── CLAUDE.md                          # Dashboard — Pipeline Status + project constraints
├── IDEA_CANDIDATES.md                 # Curated pool of viable ideas (post-review)
├── findings.md                        # Lightweight discovery log (experiments + debug)
├── EXPERIMENT_LOG.md                  # Complete record of all experiments run
├── docs/
│   └── research_contract.md           # Focused context for the active idea
├── 01_IDEA_REPORT.md                  # Canonical ranked idea report
├── 01_FINAL_PROPOSAL.md               # Canonical refined method proposal
├── 02_EXPERIMENT_PLAN.md              # Canonical experiment design (claims + blocks)
├── 02_EXPERIMENT_TRACKER.md           # Canonical execution checklist (TODO → DONE)
├── 03_AUTO_REVIEW.md                  # Canonical review loop log
├── REVIEW_STATE.json                  # Review loop recovery state
└── 04_NARRATIVE_REPORT.md             # Canonical narrative handoff into paper writing
```

### Canonical ARIS Files

| File | Created by | Purpose |
|------|-----------|---------|
| `01_IDEA_REPORT.md` | `/aris-0-2-idea-discovery` | Canonical ranked idea report with pilot results and eliminations |
| `01_FINAL_PROPOSAL.md` | `/aris-1-7-research-refine` | Canonical refined method proposal |
| `02_EXPERIMENT_PLAN.md` | `/aris-1-8-experiment-plan` | Canonical experiment design: claim map, blocks, run order, compute budget |
| `02_EXPERIMENT_TRACKER.md` | `/aris-1-8-experiment-plan` | Canonical execution checklist: run ID, status (TODO→DONE), one-line notes |
| `03_AUTO_REVIEW.md` | `/aris-3-1-auto-review-loop` | Canonical cumulative review log: scores, reviewer responses, actions taken |
| `04_NARRATIVE_REPORT.md` | `/aris-3-1-auto-review-loop` | Canonical narrative handoff into paper writing |
| `REVIEW_STATE.json` | `/aris-3-1-auto-review-loop` | Recovery state for context compaction |

### New Files (this guide)

| File | Purpose | Template |
|------|---------|----------|
| `IDEA_CANDIDATES.md` | Curated pool of viable ideas that survived review — pick next idea from here when pivoting | [`IDEA_CANDIDATES_TEMPLATE.md`](../templates/IDEA_CANDIDATES_TEMPLATE.md) |
| `findings.md` | Lightweight discovery log — anomalies, debug root causes, key decisions during experiments | [`FINDINGS_TEMPLATE.md`](../templates/FINDINGS_TEMPLATE.md) |
| `EXPERIMENT_LOG.md` | Complete experiment record — full results, configs, reproduction commands | [`EXPERIMENT_LOG_TEMPLATE.md`](../templates/EXPERIMENT_LOG_TEMPLATE.md) |
| `docs/research_contract.md` | Focused working document for the active idea (from [Session Recovery Guide](SESSION_RECOVERY_GUIDE.md)) | [`RESEARCH_CONTRACT_TEMPLATE.md`](../templates/RESEARCH_CONTRACT_TEMPLATE.md) |

## How They Relate

### Idea Flow

```
01_IDEA_REPORT.md                 (canonical ranked ideas + pilot notes)
  ↓ novelty-check + review
IDEA_CANDIDATES.md                (3-5 viable ideas, scored)
  ↓ select one
docs/research_contract.md         (active idea, focused context)
  ↓ idea fails?
IDEA_CANDIDATES.md → pick next → update contract
```

**Why three files?** Context pollution. Loading 12 raw ideas into every session wastes the LLM's working memory. The candidate pool is lean (3-5 entries), and the contract is focused (one idea). On session recovery, the LLM reads only the contract — not the full report.

### Experiment Flow

```
02_EXPERIMENT_PLAN.md             (what to run — design)
  ↓
02_EXPERIMENT_TRACKER.md          (execution status — TODO/RUNNING/DONE)
  ↓ experiment completes
EXPERIMENT_LOG.md                 (what happened — full results + reproduction)
  ↓ discover something unexpected
findings.md                       (one-line entry — anomaly, root cause, decision)
```

**Why separate tracker and log?** Different audiences. The tracker is for execution management ("what's left to run?"). The log is for knowledge preservation ("what did we learn?"). The tracker can be reset between ideas; the log is permanent.

### When to Write Each File

| File | Write when... | Update frequency |
|------|--------------|-----------------|
| `IDEA_CANDIDATES.md` | After `/aris-0-2-idea-discovery` completes (initial creation); after idea kill/selection (update status) | Per idea transition |
| `findings.md` | Discover something non-obvious during experiments, debugging, or analysis | As discoveries happen (append) |
| `EXPERIMENT_LOG.md` | An experiment finishes (any experiment, successful or not) | After every experiment |
| `docs/research_contract.md` | Select an idea to work on; baseline reproduced; major results obtained | Per stage milestone |

### Session Recovery Priority

On new session or post-compaction, read files in this order:

1. `CLAUDE.md` → Pipeline Status (30 seconds: where am I?)
2. `docs/research_contract.md` (active idea context)
3. `findings.md` recent entries (what did I discover recently?)
4. `EXPERIMENT_LOG.md` (if needed: what experiments have been run?)

Do NOT read `01_IDEA_REPORT.md` or `IDEA_CANDIDATES.md` unless switching ideas.

## Separation Principles

| Question | Answer |
|----------|--------|
| Where does a brainstorm idea go? | `01_IDEA_REPORT.md` (canonical) → `IDEA_CANDIDATES.md` (curated) |
| Where does the current idea's full context go? | `docs/research_contract.md` |
| Where does "experiment X is running" go? | `02_EXPERIMENT_TRACKER.md` |
| Where does "experiment X got accuracy 95.2" go? | `EXPERIMENT_LOG.md` |
| Where does "lr=1e-4 diverges on dataset-X" go? | `findings.md` |
| Where does "reviewer says add ablation" go? | `03_AUTO_REVIEW.md` |
| Where does "chose approach A over B because Z" go? | `findings.md` |
| Where does "current stage is training" go? | `CLAUDE.md` Pipeline Status |
