# Skill Drift Policy (base skills vs skills-codex)

This document defines how we track and govern drift between:

- base skills: `skills/aris-*/SKILL.md`
- codex mirror skills: `skills/skills-codex/aris-*/SKILL.md`

## Goals

- Make drift visible and reviewable.
- Distinguish intentional drift from accidental drift.
- Enable gradual convergence toward stronger SSOT without breaking current workflows.

## Source of truth (current phase)

- Overlay packages (`skills/skills-codex-claude-review/`, `skills/skills-codex-gemini-review/`) are generated artifacts.
- Base-vs-codex is currently tracked via drift report + allowlist.

## Tools

- Drift report script: `tools/skill_variant_drift_report.py`
- Drift allowlist: `tools/skill_variant_drift_allowlist.json`

## Commands

```bash
# Print summary only
python3 tools/skill_variant_drift_report.py

# Emit machine + human artifacts
python3 tools/skill_variant_drift_report.py \
  --json-out artifacts/skill_drift_report.json \
  --markdown-out artifacts/skill_drift_report.md \
  --priority-out artifacts/skill_drift_priority.md

# Enforce allowlist gate (fails on unallowlisted drift)
python3 tools/skill_variant_drift_report.py --check
```

## Policy rules

1. Any new base-vs-codex mismatch must be either:
   - converged (fix files), or
   - explicitly listed in `tools/skill_variant_drift_allowlist.json` with PR rationale.
2. Allowlist entries should be temporary when possible.
3. Avoid broad wildcards in allowlist; list skill names explicitly.
4. Keep overlay generation checks and drift checks both green before merge.

## Current intentional drift

See `tools/skill_variant_drift_allowlist.json`.
