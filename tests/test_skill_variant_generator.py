#!/usr/bin/env python3

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = REPO_ROOT / "tools" / "generate_skill_variants.py"
MANIFEST = REPO_ROOT / "tools" / "skill_variants_manifest.yaml"


class TestSkillVariantManifest(unittest.TestCase):
    def test_manifest_has_expected_variants(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertIn("variants", data)
        variants = data["variants"]
        self.assertIn("codex-claude-review", variants)
        self.assertEqual(len(variants), 1)
        self.assertEqual(len(variants["codex-claude-review"]["targets"]), 8)


class TestSkillVariantGenerator(unittest.TestCase):
    def run_cmd(self, *args):
        return subprocess.run(
            [sys.executable, str(GENERATOR), *args],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

    def test_list_variants(self):
        result = self.run_cmd("--list")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("codex-claude-review", result.stdout)
        self.assertIn("skills: 8", result.stdout)

    def test_check_no_drift(self):
        result = self.run_cmd("--check")
        self.assertEqual(result.returncode, 0, msg=result.stdout + "\n" + result.stderr)
        self.assertIn("ok: no drift", result.stdout)

    def test_write_is_deterministic_for_overlay_file(self):
        target = REPO_ROOT / "skills" / "skills-codex-claude-review" / "aris-4-1-paper-plan" / "SKILL.md"

        before_hash = hashlib.sha256(target.read_bytes()).hexdigest()

        first = self.run_cmd("--variant", "codex-claude-review", "--write")
        self.assertEqual(first.returncode, 0, msg=first.stdout + "\n" + first.stderr)

        second = self.run_cmd("--variant", "codex-claude-review", "--write")
        self.assertEqual(second.returncode, 0, msg=second.stdout + "\n" + second.stderr)

        after_hash = hashlib.sha256(target.read_bytes()).hexdigest()
        self.assertEqual(before_hash, after_hash)


if __name__ == "__main__":
    unittest.main()
