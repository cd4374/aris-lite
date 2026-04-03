---
name: aris-9-5-improve-loop
description: General-purpose executor-reviewer loop for common tasks. Claude Code first does the task, asks clarifying questions if needed, then Codex MCP reviews and the loop iterates until the result is strong enough or max rounds reached. Trigger with "improve", "refine", "review and improve", "ask clarifying questions and improve", or "iterate on".
argument-hint: [task-or-scope]
allowed-tools: Bash(*), Read, Grep, Glob, Write, Edit, Agent, Skill, AskUserQuestion, mcp__codex__codex, mcp__codex__codex-reply
---

# Improve Loop: General-Purpose Task Improvement

Autonomously iterate on a general task: Claude Code does the work first, Codex reviews the current result, Claude Code applies the minimum high-value fixes, and the loop repeats until the result is ready or MAX_ROUNDS is reached.

## Context: $ARGUMENTS

## Constants

- MAX_ROUNDS = 5
- POSITIVE_THRESHOLD: score >= 8/10 AND verdict explicitly indicates the result is ready. Do not stop on "almost", "close", or weak positive phrasing.
- REVIEW_DOC: `IMPROVE_LOG.md` in project root (cumulative log, canonical)
- STATE_FILE: `IMPROVE_STATE.json` in project root
- REVIEWER_MODEL = `gpt-5.4` via Codex MCP
- **HUMAN_CHECKPOINT = false** — When `true`, pause after each review round and wait for user direction before implementing the next fixes.

> Override example: `/aris-9-5-improve-loop "improve the login flow" — human checkpoint: true, max rounds: 3`

## Loop Roles

- **Executor**: Claude Code performs the task, edits code, writes the answer, or asks the user clarifying questions when needed.
- **Reviewer**: Codex MCP evaluates the current result, scores it, and proposes the minimum fixes.
- **Judge**: applies deterministic stop criteria from structured round state.

## Loop Phases

1. Understand
2. Execute
3. Review
4. Parse & prioritize
5. Improve
6. Document

## Iteration State (Compact Recovery)

Persist state to `IMPROVE_STATE.json` after each round:

```json
{
  "loop_name": "aris-9-5-improve-loop",
  "round": 2,
  "max_rounds": 5,
  "phase": "document",
  "status": "in_progress",
  "review_thread_id": "019cd392-...",
  "last_score": 7.0,
  "last_verdict": "almost",
  "open_actions": ["handle invalid input", "shorten the explanation"],
  "completed_actions": ["clarified requirements", "fixed edge-case bug"],
  "stop_reason": "",
  "updated_at": "2026-04-03T12:00:00"
}
```

**Write this file at the end of every round** after documenting the result. Overwrite each time.

**On completion**, set `"status": "completed"` with a non-empty `stop_reason`.

## Stop Criteria (ordered)

1. Success threshold reached (score + explicit ready verdict)
2. Hard max rounds reached
3. No actionable issues remain
4. Plateau for 2 consecutive rounds (no material improvement)
5. User stop via checkpoint

## Round Output Contract

Each round must append to `IMPROVE_LOG.md` and update `IMPROVE_STATE.json` with:
- score, verdict, prioritized actions
- what changed this round
- whether a user clarification was requested
- judge decision: continue/stop + `stop_reason`

## Workflow

### Initialization

1. Check for `IMPROVE_STATE.json` in project root:
   - if absent: fresh start
   - if present with `status: "completed"`: fresh start
   - if present with `status: "in_progress"` and `updated_at` older than 24 hours: fresh start
   - if present with `status: "in_progress"` and recent: resume from the next round using the saved `review_thread_id`
2. Read the current task context from `$ARGUMENTS`
3. Read any files needed for the task before proposing edits
4. If resuming, read `IMPROVE_LOG.md` to restore prior context
5. Initialize round counter = 1 unless resuming

### Loop (repeat up to MAX_ROUNDS)

#### Phase A: Understand

Understand the task and determine whether any blocking clarification is needed before execution.

Only ask the user a clarifying question when the ambiguity materially changes the output. If the best next step is obvious, proceed without asking.

If clarification is necessary, use `AskUserQuestion`, then resume the loop with the clarified direction.

#### Phase B: Execute

Produce the current best version of the result for the task.

Examples:
- for code tasks: inspect files, edit code, run focused checks if needed
- for writing tasks: draft or revise the answer directly
- for analysis tasks: gather the needed evidence, then answer

Round 1 should produce the strongest reasonable first pass before review.

#### Phase C: Review

Send the current result to Codex MCP for evaluation.

Round 1:

```text
mcp__codex__codex:
  config: {"model_reasoning_effort": "xhigh"}
  prompt: |
    [Round N/MAX_ROUNDS of an autonomous improvement loop]

    Task:
    [paste the original task from $ARGUMENTS]

    Current result:
    [paste the current answer, code diff summary, or output]

    Review this as a strict senior engineer / editor.

    1. Score the current result from 1-10 for correctness, clarity, completeness, and usefulness.
    2. State clearly whether the result is READY: Yes / No / Almost.
    3. List the remaining weaknesses ranked by severity.
    4. For each weakness, specify the MINIMUM fix.
    5. State whether any missing clarification from the user is still blocking a better result.
    6. If the result is already strong enough, say so directly.
```

Round 2+:

```text
mcp__codex__codex-reply:
  threadId: [review_thread_id from state]
  config: {"model_reasoning_effort": "xhigh"}
  prompt: |
    [Round N update]

    Since your last review, I made these changes:
    1. [change 1]
    2. [change 2]
    3. [change 3]

    Updated result:
    [paste updated answer, code diff summary, or output]

    Please re-score and re-assess.
    Same format: Score, Verdict, Remaining Weaknesses, Minimum Fixes, Blocking Clarifications.
```

#### Phase D: Parse & Prioritize

**CRITICAL: Save the FULL raw reviewer response** verbatim before summarizing it.

Extract:
- **Score** (numeric 1-10)
- **Verdict** (`ready` / `almost` / `not ready`)
- **Action items** (ranked list of minimum fixes)
- **Blocking clarification** (if any)

Stop only if score >= 8 AND Codex explicitly says the result is ready.

If Codex says a missing clarification is still blocking a better result, ask the user before continuing.

#### Human Checkpoint (if enabled)

Skip this step when `HUMAN_CHECKPOINT = false`.

When enabled, present:

```text
Round N/MAX_ROUNDS review complete.

Score: X/10 — [verdict]
Top weaknesses:
1. [weakness 1]
2. [weakness 2]
3. [weakness 3]

Suggested fixes:
1. [fix 1]
2. [fix 2]
3. [fix 3]

Options:
- "go" / "continue" → implement all suggested fixes
- custom instructions → modify the next round
- "skip 2" → skip fix #2
- "stop" → end the loop now
```

#### Phase E: Improve

Apply the highest-value fixes first.

Priority rules:
- fix correctness issues before style issues
- fix missing edge cases before cosmetic polish
- ask the user only when clarification is genuinely blocking
- prefer the smallest change that resolves the reviewer concern
- do the fix before re-reviewing; do not just promise it

#### Phase F: Document

Append to `IMPROVE_LOG.md`:

```markdown
## Round N (timestamp)

### Assessment (Summary)
- Score: X/10
- Verdict: [ready/almost/not ready]
- Key weaknesses: [bullet list]

### Reviewer Raw Response

<details>
<summary>Click to expand full reviewer response</summary>

[Paste the COMPLETE raw response here — verbatim, unedited.]

</details>

### Actions Taken
- [what was changed]

### Clarification
- [none / what was asked and answered]

### Status
- [continuing to round N+1 / stopping]
```

Write `IMPROVE_STATE.json` with current round, `review_thread_id`, score, verdict, `open_actions`, `completed_actions`, and `stop_reason`.

### Termination

When the loop ends:

1. Update `IMPROVE_STATE.json` with `"status": "completed"`
2. Write a final summary to `IMPROVE_LOG.md`
3. Return the best final result to the user directly
4. If the loop stopped at MAX_ROUNDS, list the remaining blockers briefly

## Key Rules

- ALWAYS use `config: {"model_reasoning_effort": "xhigh"}` for Codex review
- Save `review_thread_id` from the first call and use `mcp__codex__codex-reply` for later rounds
- Save the full raw reviewer response before extracting structured fields
- Read files before editing them
- Ask clarifying questions only when the ambiguity is truly blocking
- Implement the fix before asking for re-review
- Keep the loop practical; do not force extra rounds when the result is already ready
- **Large file handling**: If the Write tool fails due to file size, immediately retry using Bash (`cat << 'EOF' > file`) in chunks. Do NOT ask the user first.

## Next Steps

- Use this skill when the task is broad and the best answer benefits from one or more review-improve rounds.
- For highly specialized research or paper tasks, prefer the dedicated review-loop skills instead.
