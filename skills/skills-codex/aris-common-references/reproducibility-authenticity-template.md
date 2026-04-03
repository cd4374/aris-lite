# Reproducibility & Authenticity Evidence Template

Use this as a standalone artifact:

- Preferred filename: `07_REPRODUCIBILITY_AND_AUTHENTICITY.md`
- Stage: before final submission gate
- Rule: every headline claim/number in paper must map to verifiable evidence

---

## 1) Artifact Metadata

- Project:
- Paper title:
- Venue:
- Commit hash used for final results:
- Main experiment date range:
- Author/preparer:
- Last updated:

## 2) Environment Reproducibility

- OS / CUDA / driver:
- Python version:
- Package install command:
- Environment lockfile path (requirements/conda/poetry):
- Hardware used (GPU/CPU/RAM):

## 3) Run Commands (Exact)

### 3.1 Training
- Entrypoint:
- Command:
- Required env vars:
- Expected runtime:

### 3.2 Evaluation
- Entrypoint:
- Command:
- Metrics produced:

### 3.3 Ablations / Controls
- Commands:
- Purpose of each run:

## 4) Config + Hyperparameter Provenance

- Base config path(s):
- Final config path(s):
- Hyperparameters changed vs default:
- Random seed policy (single/multi-seed):
- Number of seeds and aggregation rule:

## 5) Data + Checkpoint Provenance

- Dataset names + versions:
- Split protocol / preprocessing:
- Data access path or download instructions:
- Checkpoint/artifact IDs (W&B/log path/object store):
- Integrity info (hash/version tag) if available:

## 6) Claim-to-Evidence Traceability (Required)

| Claim ID | Paper location | Exact claim text | Evidence source (table/fig/log/run) | Reproduced? (Y/N) | Notes |
|---|---|---|---|---|---|
| C1 | | | | | |
| C2 | | | | | |

## 7) Authenticity Audit (Anti-Fabrication)

- Any number copied from non-primary source? (must be No):
- Any missing raw source for headline metric? (must be No):
- Any claim stronger than evidence scope? (must be No):
- Consistency check passed across abstract/intro/conclusion? (Y/N):
- Evidence files inspected:

## 8) Reproducibility Outcome

- Reproduction status: `PASS` | `PARTIAL` | `FAIL`
- If PARTIAL/FAIL: exact blockers
- Minimal steps a reviewer can run in <1 hour:

## 9) Final Gate Decision Input

- Ready for submission from evidence perspective? `YES` | `NO`
- Blocking issues (if any):
- Required next action:
