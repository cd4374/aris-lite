---
name: aris-2-2-monitor-experiment
description: Monitor running experiments, check progress, detect anomalies, and suggest/apply fixes. Use when user says "check results", "is it done", "monitor", or wants experiment output.
argument-hint: [server-alias or screen-name]
allowed-tools: Bash(ssh *), Bash(echo *), Read, Write, Edit
---

# Monitor Experiment Results

Monitor: $ARGUMENTS

## Constants

- **ANOMALY_CHECK_INTERVAL = 60** — Seconds between anomaly checks for long-running experiments.
- **AUTO_FIX_CONFIDENCE_THRESHOLD = 80** — Percentage confidence required to apply fix automatically.
- **MAX_AUTO_FIX_ATTEMPTS = 2** — Maximum automatic fix attempts before escalating to user.
- **CRITICAL_ANOMALIES = ["NaN", "Inf", "OOM", "CUDA error", "divergence"]** — Anomalies that require immediate action.

## Workflow

### Step 1: Check What's Running

**SSH server:**
```bash
ssh <server> "screen -ls"
```

**Vast.ai instance** (read `ssh_host`, `ssh_port` from `vast-instances.json`):
```bash
ssh -p <PORT> root@<HOST> "screen -ls"
```

Also check vast.ai instance status:
```bash
vastai show instances
```

### Step 2: Collect Output from Each Screen
For each screen session, capture the last N lines:
```bash
ssh <server> "screen -S <name> -X hardcopy /tmp/screen_<name>.txt && tail -50 /tmp/screen_<name>.txt"
```

If hardcopy fails, check for log files or tee output.

### Step 3: Check for JSON Result Files
```bash
ssh <server> "ls -lt <results_dir>/*.json 2>/dev/null | head -20"
```

If JSON results exist, fetch and parse them:
```bash
ssh <server> "cat <results_dir>/<latest>.json"
```

### Step 3.5: Pull W&B Metrics (when `wandb: true` in CLAUDE.md)

**Skip this step entirely if `wandb` is not set or is `false` in CLAUDE.md.**

Pull training curves and metrics from Weights & Biases via Python API:

```bash
# List recent runs in the project
ssh <server> "python3 -c \"
import wandb
api = wandb.Api()
runs = api.runs('<entity>/<project>', per_page=10)
for r in runs:
    print(f'{r.id}  {r.state}  {r.name}  {r.summary.get(\"eval/loss\", \"N/A\")}')
\""

# Pull specific metrics from a run (last 50 steps)
ssh <server> "python3 -c \"
import wandb, json
api = wandb.Api()
run = api.run('<entity>/<project>/<run_id>')
history = list(run.scan_history(keys=['train/loss', 'eval/loss', 'eval/ppl', 'train/lr'], page_size=50))
print(json.dumps(history[-10:], indent=2))
\""

# Pull run summary (final metrics)
ssh <server> "python3 -c \"
import wandb, json
api = wandb.Api()
run = api.run('<entity>/<project>/<run_id>')
print(json.dumps(dict(run.summary), indent=2, default=str))
\""
```

**What to extract:**
- **Training loss curve** — is it converging? diverging? plateauing?
- **Eval metrics** — loss, PPL, accuracy at latest checkpoint
- **Learning rate** — is the schedule behaving as expected?
- **GPU memory** — any OOM risk?
- **Run status** — running / finished / crashed?

**W&B dashboard link** (include in summary for user):
```
https://wandb.ai/<entity>/<project>/runs/<run_id>
```

> This gives the auto-review-loop richer signal than just screen output — training dynamics, loss curves, and metric trends over time.

### Step 3.6: Anomaly Detection (CRITICAL)

**Check for training anomalies in the output/logs:**

```bash
# Check for NaN/Inf in recent log lines
ssh <server> "tail -100 <log_file> | grep -E 'NaN|Inf|nan|inf|divergence'"

# Check for OOM errors
ssh <server> "tail -100 <log_file> | grep -E 'OOM|out of memory|CUDA out of memory'"

# Check for CUDA errors
ssh <server> "tail -100 <log_file> | grep -E 'CUDA error|cudaError|device-side assert'"

# Check loss trend (if parseable)
ssh <server> "tail -50 <log_file> | grep -E 'loss.*[0-9]' | tail -10"
```

**Anomaly Detection Checklist:**

| Anomaly Type | Detection Pattern | Severity | Immediate Action |
|--------------|-------------------|----------|------------------|
| NaN/Inf loss | `loss: nan` or `NaN` in log | CRITICAL | Kill process, diagnose |
| Loss explosion | Loss > 10x initial value | CRITICAL | Kill process, reduce LR |
| Loss plateau | No decrease for 100+ steps | WARNING | Check LR, optimizer |
| OOM | `CUDA out of memory` | CRITICAL | Reduce batch size |
| CUDA error | `CUDA error`, `device-side assert` | CRITICAL | Kill process, debug code |
| Divergence | Loss oscillating wildly | WARNING | Reduce LR, add grad clip |
| Process died | Screen session empty | CRITICAL | Check crash log |

**If CRITICAL anomaly detected:**

1. **Record anomaly immediately** in `ANOMALY_LOG.md`:
   ```markdown
   | Timestamp | Experiment | Anomaly | Log Evidence | Action Taken |
   |-----------|------------|---------|---------------|--------------|
   | 2026-04-03 10:05 | exp_baseline | NaN at step 500 | logs/exp_baseline.log:500 | killed, diagnosing |
   ```

2. **Kill the problematic process** (optional, based on severity):
   ```bash
   ssh <server> "screen -S <exp_name> -X quit"
   ```

3. **Generate diagnosis**:
   ```
   🔴 CRITICAL ANOMALY: [type]

   Experiment: [name]
   Evidence: [log excerpt]
   Likely cause: [diagnosis]

   Recommended fix:
   1. [Specific fix with confidence level]
   2. [Alternative fix]

   Auto-fix confidence: X%
   ```

4. **Apply fix automatically if confidence > AUTO_FIX_CONFIDENCE_THRESHOLD**:
   - For NaN: restart with `--lr 0.5x --grad_clip 1.0`
   - For OOM: restart with `--batch_size 0.5x`
   - For CUDA error: require manual code fix (cannot auto-fix)

5. **If confidence < threshold OR MAX_AUTO_FIX_ATTEMPTS exhausted**:
   ```
   ❌ Cannot auto-fix. Requires manual intervention.

   Anomaly: [type]
   Diagnosis: [likely cause]
   Suggested investigation:
   1. Check [specific code section]
   2. Verify [specific configuration]
   3. Run [diagnostic command]

   Waiting for user decision.
   ```

### Step 4: Summarize Results

Present results in a comparison table:
```
| Experiment | Metric | Delta vs Baseline | Status |
|-----------|--------|-------------------|--------|
| Baseline  | X.XX   | —                 | done   |
| Method A  | X.XX   | +Y.Y              | done   |
```

### Step 5: Interpret
- Compare against known baselines
- Flag unexpected results (negative delta, NaN, divergence)
- Suggest next steps based on findings

## Watchdog Integration (Optional but Useful)

If `tools/watchdog.py` is running on the target server, always check:

```bash
ssh <server> "cat /tmp/aris-watchdog/status/summary.txt"
ssh <server> "tail -20 /tmp/aris-watchdog/alerts.log"
```

Use watchdog as 24/7 health signal (DEAD/IDLE/STALLED/SLOW), and use this skill for deeper diagnosis and result interpretation.

## Key Rules

- **Anomaly detection is MANDATORY** — check every monitoring cycle
- **CRITICAL anomalies require immediate action** — do not let NaN/OOM runs continue
- **Auto-fix only when confident** — wrong fix can waste more GPU hours
- **Always show raw numbers before interpretation**
- **Compare against the correct baseline** (same config)
- **Note if experiments are still running** (check progress bars, iteration counts)
- **If results look wrong, check training logs for errors before concluding**
- **Document all anomalies and fixes** — for future learning and debugging
- **Vast.ai cost awareness**: When monitoring vast.ai instances, report the running cost (hours * $/hr from `vast-instances.json`). If all experiments on an instance are done, remind the user to run `/aris-2-5-vast-gpu destroy <instance_id>` to stop billing
- **Never fabricate results** — if monitoring fails or no output available, report "no data" rather than guessing
