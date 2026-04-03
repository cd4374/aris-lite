#!/usr/bin/env python3

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "tools" / "skill_variant_drift_report.py"
ALLOWLIST = REPO_ROOT / "tools" / "skill_variant_drift_allowlist.json"


class TestSkillVariantDriftReport(unittest.TestCase):
    def run_cmd(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )

    def test_report_outputs_json_and_priority_markdown(self):
        with tempfile.TemporaryDirectory() as td:
            json_out = Path(td) / "drift.json"
            priority_out = Path(td) / "priority.md"
            result = self.run_cmd("--json-out", str(json_out), "--priority-out", str(priority_out))

            self.assertEqual(result.returncode, 0, msg=result.stdout + "\n" + result.stderr)
            self.assertIn("drift summary:", result.stdout)

            payload = json.loads(json_out.read_text(encoding="utf-8"))
            self.assertIn("report", payload)
            self.assertIn("unallowlisted", payload)
            self.assertIn("category_buckets", payload["report"])
            self.assertIn("priorities", payload["report"])
            self.assertIn("substantial_top", payload["report"])

            self.assertEqual(payload["report"]["base_count"], 45)
            self.assertEqual(payload["report"]["codex_count"], 42)
            self.assertEqual(len(payload["report"]["missing_in_codex"]), 3)
            self.assertEqual(len(payload["report"]["content_diff"]), 0)
            self.assertEqual(len(payload["report"]["same_content"]), 42)

            priority_text = priority_out.read_text(encoding="utf-8")
            self.assertIn("convergence priority", priority_text)
            self.assertIn("Category counts", priority_text)
            self.assertIn("Priority list", priority_text)
            self.assertIn("Top substantial diffs", priority_text)
            self.assertIn("Suggested convergence order", priority_text)

    def test_check_passes_with_current_allowlist(self):
        result = self.run_cmd("--check", "--allowlist", str(ALLOWLIST))
        self.assertEqual(result.returncode, 0, msg=result.stdout + "\n" + result.stderr)

    def test_check_fails_with_stale_allowlist(self):
        with tempfile.TemporaryDirectory() as td:
            stale_allowlist = Path(td) / "stale_allowlist.json"
            stale_allowlist.write_text(
                json.dumps(
                    {
                        "missing_in_codex": [
                            "aris-1-3-semantic-scholar",
                            "aris-2-5-vast-gpu"
                        ],
                        "extra_in_codex": [],
                        "content_diff": [],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            result = self.run_cmd("--check", "--allowlist", str(stale_allowlist))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unallowlisted drift detected", result.stderr)

    def test_check_passes_with_full_temporary_allowlist(self):
        with tempfile.TemporaryDirectory() as td:
            full_allowlist = Path(td) / "allowlist.json"
            full_allowlist.write_text(
                json.dumps(
                    {
                        "missing_in_codex": [
                            "aris-1-3-semantic-scholar",
                            "aris-2-5-vast-gpu",
                            "aris-9-4-system-profile",
                        ],
                        "extra_in_codex": [],
                        "content_diff": [
                            "aris-0-2-idea-discovery",
                            "aris-1-1-research-lit",
                            "aris-1-2-arxiv",
                            "aris-1-4-idea-creator",
                            "aris-1-5-novelty-check",
                            "aris-1-6-research-review",
                            "aris-1-7-research-refine",
                            "aris-1-8-experiment-plan",
                            "aris-1-9-research-refine-pipeline",
                            "aris-2-1-run-experiment",
                            "aris-2-2-monitor-experiment",
                            "aris-2-3-training-check",
                            "aris-2-4-ablation-planner",
                            "aris-3-3-analyze-results",
                            "aris-4-2-paper-figure",
                            "aris-4-3-paper-illustration",
                            "aris-4-5-paper-compile",
                            "aris-5-1-rebuttal",
                            "aris-8-2-comm-lit-review",
                            "aris-8-3-dse-loop",
                            "aris-8-4-formula-derivation",
                            "aris-8-5-proof-writer",
                            "aris-9-1-feishu-notify",
                            "aris-9-2-mermaid-diagram",
                            "aris-9-3-pixel-art",
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            result = self.run_cmd("--check", "--allowlist", str(full_allowlist))
            self.assertEqual(result.returncode, 0, msg=result.stdout + "\n" + result.stderr)


if __name__ == "__main__":
    unittest.main()
