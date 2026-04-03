---
name: aris-3-2-result-to-claim
description: Use when experiments complete to judge what claims the results support, what they don't, and what evidence is still missing. Codex MCP evaluates results against intended claims and routes to next action (pivot, supplement, or confirm). Use after experiments finish — before writing the paper or running ablations.
argument-hint: [experiment-description-or-wandb-run]
allowed-tools: Bash(*), Read, Grep, Glob, Write, Edit, mcp__codex__codex, mcp__codex__codex-reply
---

# Result-to-Claim Gate

Experiments produce numbers; this gate decides what those numbers *mean*. Collect results from available sources, build an explicit evidence packet, get a Codex judgment, then auto-route based on the verdict.

## Constants

- **MAX_REFINEMENT_ROUNDS = 2** — For `partial` support, maximum supplementary experiment → re-judge cycles before forcing a decision (narrow claim or pivot).
- **SELF_REFLECT_BEFORE_JUDGE = true** — When `true`, evaluate evidence packet quality before sending to Codex. Detects incomplete evidence collection early.
- **REQUIRE_EXPERIMENT_EVIDENCE = true** — When `true`, refuse to proceed without actual experiment run evidence. Must provide: W&B run ID, log file path with timestamp, or JSON result file. **This prevents fabrication.**

## Context: $ARGUMENTS

## When to Use

- After a set of experiments completes (main results, not just sanity checks)
- Before committing to claims in a paper or review response
- When results are ambiguous and you need an objective second opinion

## Workflow

### Step 0: Experiment Evidence Verification (CRITICAL — Anti-Fabrication)

**Before collecting any results, verify that actual experiments were run.**

This gate exists specifically to prevent fabrication of results.

Check for evidence in priority order:

1. **W&B runs** (highest trust):
   - Query W&B API for runs in the project
   - Verify run state is `finished` or `running` (not just `crashed` without data)
   - Record run ID, timestamps, final metrics

2. **Log files with creation timestamps**:
   - Check file exists: `ls -l logs/*.log results/*.json`
   - Verify creation time is recent (within expected experiment window)
   - Check file is non-empty: `wc -l <file>`

3. **Screen sessions** (for running experiments):
   - `screen -ls` shows active session
   - Hardcopy shows training progress (not just empty or error)

4. **EXPERIMENT_TRACKER.md** (fallback):
   - Has `status: DONE` entry
   - Cross-reference with actual files/W&B

**If NO evidence found**:

```
🚫 FABRICATION BLOCKED

Cannot proceed to claim judgment because no actual experiment evidence was found.

Evidence checked:
- W&B: [no runs / crashed runs only]
- Log files: [none found / empty files]
- Screen sessions: [none / empty]
- EXPERIMENT_TRACKER: [no DONE entries]

REQUIRED ACTION:
You must run experiments first:
  /aris-2-1-run-experiment "[experiment description]"

DO NOT proceed without actual experiment evidence.
Claim judgments without real experiments are fabrication.
```

**Stop completely. Do NOT generate any results or claims.**

This gate is the primary defense against result fabrication.

### Step 1: Collect Results

Gather experiment data from whatever sources are available in the project:

1. **W&B** (preferred): `wandb.Api().run("<entity>/<project>/<run_id>").history()` — metrics, training curves, comparisons
2. **EXPERIMENT_LOG.md**: full results table with baselines and verdicts
3. **02_EXPERIMENT_TRACKER.md** (fallback: `EXPERIMENT_TRACKER.md`): check which experiments are DONE vs still running
4. **Log files**: `ssh server "tail -100 /path/to/training.log"` if no other source
5. **docs/research_contract.md**: intended claims and experiment design

Assemble the key information as an explicit evidence packet:

## Evidence Packet
### Intended Claim
### Claim Type
### Experiments Run
### Exact Results
### Baselines and Source Quality
### Controls / Ablations Present
### Known Confounds
### Rival Explanations Still Open
### Scope Limits

### Step 1.5: Self-Reflection on Evidence Packet (when SELF_REFLECT_BEFORE_JUDGE = true)

**Skip entirely if `SELF_REFLECT_BEFORE_JUDGE` is `false`.**

Before sending to Codex, critically evaluate the evidence packet you assembled:

1. **Completeness check**:
   - Did we collect ALL available results or just convenient ones?
   - Are negative/null results included, not just positive ones?
   - Did we check W&B, logs, AND tracker files, not just one source?

2. **Quality check**:
   - Are baseline numbers from reproduced runs or copied from papers?
   - Is the intended claim actually what the experiment design was testing?
   - Are known confounds honestly listed, not minimized?

3. **Gap identification**:
   - What evidence is missing that we COULD have collected but didn't?
   - What comparisons are absent that a reviewer would ask for?
   - What scope limits are we glossing over?

4. **Self-score the evidence packet**:
   - Completeness: X/10
   - Honesty: X/10
   - Reviewer-readiness: X/10

If any score < 7, go back to Step 1 and collect more evidence before proceeding. Document the self-reflection in `findings.md` under "Evidence Packet Self-Reflection".

### Step 2: Codex Judgment

Send the collected results to Codex for objective evaluation:

```
mcp__codex__codex:
  config: {"model_reasoning_effort": "xhigh"}
  prompt: |
    RESULT-TO-CLAIM EVALUATION

    I need you to judge whether experimental results support the intended claim.

    Intended claim: [the claim these experiments test]

    Experiments run:
    [list experiments with method, dataset, metrics]

    Results:
    [paste key numbers, comparison deltas, significance]

    Baselines:
    [baseline numbers and sources — reproduced or from paper]

    Known caveats:
    [any confounding factors, limited datasets, missing comparisons]

    Please evaluate:
    1. claim_supported: yes | partial | no
    2. support_level_by_scope: narrow | moderate | broad
    3. direct_evidence: which results directly support the claim
    4. indirect_evidence: what is suggestive but not decisive
    5. what_results_dont_support: where the data falls short of the claim
    6. unsupported_leaps: where the intended claim goes beyond the evidence
    7. alternative_explanations_remaining: rival explanations still not ruled out
    8. missing_controls: controls or ablations still required
    9. missing_evidence: specific evidence gaps
    10. max_safe_claim: strongest claim that is actually justified now
    11. claim_revision: if the claim should be strengthened, weakened, or reframed
    12. next_experiments_needed: specific experiments to fill gaps (if any)
    13. confidence: high | medium | low

    Be honest. Do not inflate claims beyond what the data supports.
    A single positive result on one dataset does not support a general claim.
```

### Step 3: Parse and Normalize

Extract structured fields from Codex response into a fixed claim judgment block.

Add a **judge-compatible verdict block** for downstream loops/gates:
- `status`: `supported` | `partial` | `unsupported`
- `blocking_issues`: explicit list of evidence blockers
- `next_action`: `proceed_to_paper` | `run_supplementary_experiments` | `pivot`
- `stop_reason`: concise machine-readable reason (e.g., `insufficient_controls`, `weak_scope_support`)

This keeps routing semantics aligned with Reviewer→Optimizer→Judge loops.

Extract structured fields from Codex response into a fixed claim judgment block:

```markdown
## Claim Judgment
- claim_supported: yes | partial | no
- support_level_by_scope: narrow | moderate | broad
- direct_evidence: "..."
- indirect_evidence: "..."
- what_results_dont_support: "..."
- unsupported_leaps: "..."
- alternative_explanations_remaining: "..."
- missing_controls: "..."
- missing_evidence: "..."
- max_safe_claim: "..."
- claim_revision: "..."
- next_experiments_needed: "..."
- confidence: high | medium | low
```

### Step 4: Route Based on Verdict

#### `no` — Claim not supported

1. Record postmortem in findings.md (Research Findings section):
   - What was tested, what failed, hypotheses for why
   - Constraints for future attempts (what NOT to try again)
2. Update CLAUDE.md Pipeline Status
3. Decide whether to pivot to next idea from IDEA_CANDIDATES.md or try an alternative approach

#### `partial` — Claim partially supported

1. Update the working claim to reflect what IS supported
2. Record the gap in findings.md
3. Design and run supplementary experiments to fill evidence gaps
4. Re-run result-to-claim after supplementary experiments complete
5. **Refinement round tracking**: Increment round counter. If round > MAX_REFINEMENT_ROUNDS:
   - Force decision: either narrow claim to what IS supported (record as `narrow_confirmed`) or pivot to next idea
   - Do NOT continue cycling indefinitely
6. Document refinement history in `CLAIM_REFINEMENT_LEDGER.md`:
   ```markdown
   | Round | Support Level | Gap Identified | Experiment Added | Result | Decision |
   |-------|---------------|----------------|------------------|--------|----------|
   | 1 | partial | missing baseline X | run baseline X | Y% delta | continue |
   | 2 | partial | narrow scope | (none) | — | narrow claim |
   ```

#### `yes` — Claim supported

1. Record confirmed claim in project notes
2. If ablation studies are incomplete → trigger `/aris-2-4-ablation-planner`
3. If all evidence is in → ready for paper writing

## Rules

- **NEVER FABRICATE RESULTS.** Step 0 is a hard gate. If no experiment evidence exists, stop completely. Do not generate any numbers, claims, or judgments without real experiment output.
- **Every numeric result must have a source.** Record W&B run ID, log file path, or JSON file for every number used in the judgment.
- **Codex is the judge, not CC.** CC collects evidence and routes; Codex evaluates. This prevents post-hoc rationalization.
- Do not inflate claims beyond what the data supports. If Codex says "partial", do not round up to "yes".
- A single positive result on one dataset does not support a general claim. Be honest about scope.
- If `unsupported_leaps` is non-empty, do not allow paper-ready claim language yet.
- If `alternative_explanations_remaining` includes a core rival explanation, route to supplementary experiments even when topline results are positive.
- If `support_level_by_scope` is `narrow`, explicitly narrow downstream claim wording to match.
- If `confidence` is low, treat the judgment as inconclusive and add experiments rather than committing to a claim.
- If Codex MCP is unavailable (call fails), CC makes its own judgment and marks it `[pending Codex review]` — do not block the pipeline.
- Always record the verdict and reasoning in findings.md, regardless of outcome.
