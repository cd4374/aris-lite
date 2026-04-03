---
name: aris-3-3-analyze-results
description: Analyze ML experiment results, compute statistics, generate comparison tables and insights. Use when user says "analyze results", "compare", or needs to interpret experimental data.
argument-hint: [results-path-or-description]
allowed-tools: Bash(*), Read, Grep, Glob, Write, Edit, Agent
---

# Analyze Experiment Results

Analyze: $ARGUMENTS

## Constants

- **REQUIRE_EXPERIMENT_EVIDENCE = true** — When `true`, refuse to generate results without actual experiment run evidence. Must provide: W&B run ID, log file path, screen session name, or JSON result file with timestamp.
- **FABRICATION_CHECK = true** — When `true`, verify all numeric results trace back to actual experiment outputs. Any untraceable number must be flagged, not guessed.
- **MAX_AUTO_FIX_ATTEMPTS = 2** — For detected anomalies (NaN, divergence), attempt automatic fix suggestions up to 2 rounds before escalating to user.

## Workflow

### Step 0: Experiment Evidence Verification (CRITICAL)

**Before any analysis, verify that actual experiments were run.**

Check for experiment evidence in this priority order:

1. **W&B runs** (most trusted):
   ```bash
   # Check if W&B project exists and has recent runs
   python3 -c "
   import wandb
   api = wandb.Api()
   runs = api.runs('<entity>/<project>', per_page=5)
   for r in runs:
       print(f'{r.id} | {r.state} | {r.name} | created: {r.created_at}')
   "
   ```
   - If found: record W&B run IDs as evidence source
   - If not found → check local logs

2. **Log files with timestamps**:
   ```bash
   ls -lt logs/*.log results/*.json 2>/dev/null | head -10
   ```
   - If found: check file creation time matches expected experiment time
   - If not found → check screen sessions

3. **Screen sessions** (still running):
   ```bash
   ssh <server> "screen -ls" 2>/dev/null || screen -ls
   ```
   - If found: extract output via hardcopy, record screen name
   - If not found → NO EXPERIMENT EVIDENCE

4. **EXPERIMENT_TRACKER.md** (fallback):
   - Check for `status: DONE` entries with timestamps
   - Cross-reference with actual files

**If NO evidence found**:

```
🚫 NO EXPERIMENT EVIDENCE DETECTED

Cannot analyze results because no actual experiment run was found.

Evidence checked:
- W&B: no runs in <entity>/<project>
- Log files: none in logs/ or results/
- Screen sessions: none found
- EXPERIMENT_TRACKER.md: no DONE entries

REQUIRED ACTION:
1. Run the experiment first: /aris-2-1-run-experiment "<experiment description>"
2. Or provide actual result files/log paths if they exist elsewhere

DO NOT proceed with analysis until experiment evidence is confirmed.
```

**Stop and do NOT generate any numeric results** until evidence is confirmed.

### Step 1: Locate Results
Find all relevant JSON/CSV result files:
- Check `figures/`, `results/`, or project-specific output directories
- Parse JSON results into structured data
- **Record evidence source for each result file**: (W&B run ID, log path, screen name, or JSON file path)

### Step 2: Build Comparison Table
Organize results by:
- **Independent variables**: model type, hyperparameters, data config
- **Dependent variables**: primary metric (e.g., perplexity, accuracy, loss), secondary metrics
- **Delta vs baseline**: always compute relative improvement

### Step 3: Statistical Analysis + Anomaly Detection

**Standard analysis:**
- If multiple seeds: report mean +/- std, check reproducibility
- If sweeping a parameter: identify trends (monotonic, U-shaped, plateau)
- Flag outliers or suspicious results

**Anomaly detection (auto-check):**
For each metric, check for:

1. **NaN/Inf values** → training divergence
   - Action: Check learning rate, gradient clipping, data preprocessing

2. **Loss not decreasing** → optimization failure
   - Action: Check learning rate schedule, batch size, model architecture

3. **Loss exploding** → instability
   - Action: Reduce LR, add gradient clipping, check for numerical issues

4. **OOM (Out of Memory)** → resource limit
   - Action: Reduce batch size, use gradient accumulation, model parallelism

5. **Metric worse than baseline** → negative signal
   - Action: Check if implementation matches intended method, verify hyperparams

6. **Suspiciously good results** (e.g., +50% improvement on established benchmark) → possible bug
   - Action: Verify evaluation code, check for data leakage, run on held-out test

**If anomaly detected:**

```markdown
⚠️ ANOMALY DETECTED: [type]

Evidence: [specific numbers/log lines]
Diagnosis: [likely cause]
Suggested fix: [concrete action]

Auto-fix attempt 1/N:
[Specific fix suggestion with command]

Apply fix? Or manual intervention needed?
```

### Step 3.5: Auto-Fix Loop (when anomaly detected)

If anomaly detected and MAX_AUTO_FIX_ATTEMPTS > 0:

1. **Generate fix suggestion** based on anomaly type:

| Anomaly | Common Fixes |
|---------|--------------|
| NaN/Inf | Reduce LR (×0.5), add gradient clipping (1.0), check fp16 |
| Loss plateau | Increase LR, check warmup, verify optimizer params |
| Loss exploding | Reduce LR (×0.1), add grad clip, check for division by zero |
| OOM | Reduce batch size (×0.5), gradient accumulation, empty cache |
| Worse than baseline | Check implementation diff, verify hyperparams match paper |
| Suspiciously good | Run eval on separate test set, check data leakage |

2. **Apply fix automatically if confidence > 80%**:
   - For LR issues: suggest new LR value based on observed behavior
   - For OOM: calculate max batch size given memory usage
   - For implementation: point to specific line to check

3. **Re-run experiment with fix**:
   ```
   /aris-2-1-run-experiment "<experiment> — fix: [anomaly fix]"
   ```

4. **Track fix attempts in `ANOMALY_FIX_LOG.md`**:
   ```markdown
   | Timestamp | Anomaly | Fix Attempted | Result | Status |
   |-----------|---------|---------------|--------|--------|
   | 2026-04-03 10:00 | NaN at step 500 | LR 1e-4 → 5e-5, grad_clip=1.0 | converged | FIXED |
   | 2026-04-03 11:00 | OOM | batch_size 64 → 32 | runs | FIXED |
   ```

5. **If MAX_AUTO_FIX_ATTEMPTS exhausted without resolution**:
   ```
   ❌ AUTO-FIX FAILED after N attempts

   Anomaly: [type]
   Fixes tried: [list]
   All failed.

   Requires manual investigation. Suggestions:
   1. [Specific diagnostic to run]
   2. [Code section to inspect]
   3. [Alternative approach]

   Escalating to user.
   ```

### Step 4: Generate Insights
For each finding, structure as:
1. **Observation**: what the data shows (with numbers)
2. **Interpretation**: why this might be happening
3. **Implication**: what this means for the research question
4. **Next step**: what experiment would test the interpretation

### Step 5: Update Documentation
If findings are significant:
- Propose updates to project notes or experiment reports
- Draft a concise finding statement (1-2 sentences)

## Output Format
Always include:
1. **Evidence Sources** table (required for FABRICATION_CHECK):
   ```
   | Result | Evidence Source | Timestamp | Verified |
   |--------|-----------------|-----------|----------|
   | baseline.json | W&B run abc123 | 2026-04-03 10:00 | ✓ |
   | method_a.json | logs/exp_a.log | 2026-04-03 11:30 | ✓ |
   ```

2. Raw data table with evidence trace

3. Key findings (numbered, concise, with evidence reference)

4. Anomaly report (if any detected)

5. Suggested next experiments (if any)

## Key Rules

- **NEVER generate numeric results without experiment evidence** — this is fabrication
- **Every number must trace to a source**: W&B run ID, log file line, JSON file path
- **If evidence is missing, STOP** — do not guess or extrapolate
- **Anomaly detection is mandatory** — catch training issues early
- **Auto-fix is optional** — apply only when fix confidence is high
- **Document all anomaly fixes** — for future reference and learning
- **Suspiciously good results require extra verification** — check for bugs before claiming success
