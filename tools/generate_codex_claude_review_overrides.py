#!/usr/bin/env python3
"""Compatibility wrapper: generate Claude-review overrides via unified generator."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    generator = repo_root / "tools" / "generate_skill_variants.py"
    cmd = [sys.executable, str(generator), "--variant", "codex-claude-review", "--write"]
    result = subprocess.run(cmd, check=False)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
