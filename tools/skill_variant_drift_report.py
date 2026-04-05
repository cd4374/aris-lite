#!/usr/bin/env python3
"""Report drift between base skills/ and skills-codex/.

This tool is informational by default. Use --check to fail on unallowlisted drift.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)

PRIORITY_SCORE = {
    "tool_mapping_only": 1,
    "metadata_only": 2,
    "mixed": 3,
    "substantial": 4,
}

CATEGORY_LABELS = {
    "tool_mapping_only": "Tool mapping only",
    "metadata_only": "Frontmatter/metadata only",
    "mixed": "Mixed (metadata + tool mapping)",
    "substantial": "Substantial body differences",
}


def split_frontmatter_body(text: str) -> tuple[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return "", text
    return match.group(1), text[match.end():]


def normalize_tool_tokens(text: str) -> str:
    text = re.sub(r"mcp__codex__codex-reply", "<REVIEW_REPLY_TOOL>", text)
    text = re.sub(r"mcp__codex__codex", "<REVIEW_TOOL>", text)
    text = re.sub(r"mcp__claude-review__review_reply_start", "<REVIEW_REPLY_TOOL>", text)
    text = re.sub(r"mcp__claude-review__review_start", "<REVIEW_TOOL>", text)
    return text


def classify_diff(base_text: str, codex_text: str) -> str:
    base_fm, base_body = split_frontmatter_body(base_text)
    codex_fm, codex_body = split_frontmatter_body(codex_text)

    base_body_norm = normalize_tool_tokens(base_body)
    codex_body_norm = normalize_tool_tokens(codex_body)

    metadata_diff = base_fm.strip() != codex_fm.strip()
    body_diff = base_body != codex_body
    tool_only_diff = base_body_norm == codex_body_norm and body_diff

    if metadata_diff and not body_diff:
        return "metadata_only"
    if tool_only_diff and not metadata_diff:
        return "tool_mapping_only"
    if tool_only_diff and metadata_diff:
        return "mixed"
    return "substantial"


def priority_from_category(category: str) -> int:
    return PRIORITY_SCORE.get(category, 5)


def build_category_buckets(content_diff_details: dict[str, dict]) -> dict[str, list[str]]:
    buckets = {
        "tool_mapping_only": [],
        "metadata_only": [],
        "mixed": [],
        "substantial": [],
    }
    for skill, detail in content_diff_details.items():
        category = detail["category"]
        buckets.setdefault(category, []).append(skill)
    for key in buckets:
        buckets[key].sort()
    return buckets


def prioritized_items(content_diff_details: dict[str, dict]) -> list[dict]:
    rows: list[dict] = []
    for skill, detail in sorted(content_diff_details.items()):
        category = detail["category"]
        rows.append(
            {
                "skill": skill,
                "category": category,
                "category_label": CATEGORY_LABELS.get(category, category),
                "priority": priority_from_category(category),
            }
        )
    rows.sort(key=lambda x: (x["priority"], x["skill"]))
    return rows


def count_diff_lines(a: str, b: str) -> int:
    diff = difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="")
    changed = 0
    for line in diff:
        if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
            continue
        if line.startswith("+") or line.startswith("-"):
            changed += 1
    return changed


def summarize_top_substantial_changes(content_diff_details: dict[str, dict], top_n: int = 10) -> list[dict]:
    rows: list[dict] = []
    for skill, detail in content_diff_details.items():
        if detail["category"] != "substantial":
            continue
        rows.append({
            "skill": skill,
            "changed_lines": detail.get("changed_lines", 0),
        })
    rows.sort(key=lambda x: (-x["changed_lines"], x["skill"]))
    return rows[:top_n]


def classify_all_diffs(base: dict[str, Path], codex: dict[str, Path], diff_skills: list[str]) -> dict[str, dict]:
    details: dict[str, dict] = {}
    for skill in diff_skills:
        base_text = base[skill].read_text(encoding="utf-8")
        codex_text = codex[skill].read_text(encoding="utf-8")
        category = classify_diff(base_text, codex_text)
        details[skill] = {
            "category": category,
            "changed_lines": count_diff_lines(base_text, codex_text),
        }
    return details


def compare_skill_maps(base: dict[str, Path], codex: dict[str, Path]) -> dict:
    base_names = set(base.keys())
    codex_names = set(codex.keys())

    missing_in_codex = sorted(base_names - codex_names)
    extra_in_codex = sorted(codex_names - base_names)

    same_content: list[str] = []
    content_diff: list[str] = []

    for name in sorted(base_names & codex_names):
        if sha256_text(base[name]) == sha256_text(codex[name]):
            same_content.append(name)
        else:
            content_diff.append(name)

    content_diff_details = classify_all_diffs(base, codex, content_diff)
    category_buckets = build_category_buckets(content_diff_details)
    priorities = prioritized_items(content_diff_details)
    substantial_top = summarize_top_substantial_changes(content_diff_details)

    return {
        "missing_in_codex": missing_in_codex,
        "extra_in_codex": extra_in_codex,
        "same_content": same_content,
        "content_diff": content_diff,
        "content_diff_details": content_diff_details,
        "category_buckets": category_buckets,
        "priorities": priorities,
        "substantial_top": substantial_top,
    }


def build_priority_suggestions(report: dict) -> list[str]:
    buckets = report.get("category_buckets", {})
    lines: list[str] = []

    tool_only = len(buckets.get("tool_mapping_only", []))
    metadata_only = len(buckets.get("metadata_only", []))
    mixed = len(buckets.get("mixed", []))
    substantial = len(buckets.get("substantial", []))

    if tool_only:
        lines.append(f"P1: Converge {tool_only} tool-mapping-only skills via automated rewrite rules first.")
    if metadata_only:
        lines.append(f"P2: Normalize frontmatter/metadata for {metadata_only} skills using scripted fields sync.")
    if mixed:
        lines.append(f"P3: Resolve {mixed} mixed diffs after P1/P2 to avoid duplicate manual edits.")
    if substantial:
        lines.append(f"P4: Review {substantial} substantial diffs manually in small batches by workflow domain.")

    if not lines:
        lines.append("No convergence actions needed.")
    return lines


def render_priority_markdown(report: dict) -> str:
    lines: list[str] = []
    lines.append("# skills vs skills-codex convergence priority")
    lines.append("")

    buckets = report.get("category_buckets", {})
    lines.append("## Category counts")
    for key in ("tool_mapping_only", "metadata_only", "mixed", "substantial"):
        lines.append(f"- {CATEGORY_LABELS[key]}: {len(buckets.get(key, []))}")
    lines.append("")

    lines.append("## Suggested convergence order")
    for item in build_priority_suggestions(report):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Priority list")
    for row in report.get("priorities", []):
        lines.append(f"- P{row['priority']} `{row['skill']}` — {row['category_label']}")
    lines.append("")

    lines.append("## Top substantial diffs (by changed lines)")
    top_substantial = report.get("substantial_top", [])
    if not top_substantial:
        lines.append("- none")
    else:
        for row in top_substantial:
            lines.append(f"- `{row['skill']}` — {row['changed_lines']} changed lines")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_ROOT = REPO_ROOT / "skills"
DEFAULT_CODEX_ROOT = REPO_ROOT / "skills" / "skills-codex"
DEFAULT_ALLOWLIST = REPO_ROOT / "tools" / "skill_variant_drift_allowlist.json"


def sha256_text(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_skill_files(root: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for path in sorted(root.glob("aris-*/SKILL.md")):
        skill_name = path.parent.name
        result[skill_name] = path
    return result


def load_allowlist(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        return {"missing_in_codex": [], "extra_in_codex": [], "content_diff": []}

    payload = json.loads(path.read_text(encoding="utf-8"))
    for key in ("missing_in_codex", "extra_in_codex", "content_diff"):
        if key not in payload:
            payload[key] = []
        payload[key] = sorted(set(payload[key]))
    return payload


def compute_drift(base_root: Path, codex_root: Path) -> dict:
    base = collect_skill_files(base_root)
    codex = collect_skill_files(codex_root)

    compared = compare_skill_maps(base, codex)

    return {
        "base_count": len(base),
        "codex_count": len(codex),
        **compared,
    }


def subtract_allowlist(items: list[str], allowed: list[str]) -> list[str]:
    allowed_set = set(allowed)
    return [item for item in items if item not in allowed_set]


def render_markdown(report: dict, allowlist: dict, unallowlisted: dict) -> str:
    lines: list[str] = []
    lines.append("# skills vs skills-codex drift report")
    lines.append("")
    lines.append(f"- base skills (`skills/aris-*`): **{report['base_count']}**")
    lines.append(f"- codex skills (`skills/skills-codex/aris-*`): **{report['codex_count']}**")
    lines.append(f"- exact-match skills: **{len(report['same_content'])}**")
    lines.append(f"- content-diff skills: **{len(report['content_diff'])}**")
    lines.append("")

    lines.append("## Drift summary")
    lines.append(f"- missing in codex: {len(report['missing_in_codex'])}")
    lines.append(f"- extra in codex: {len(report['extra_in_codex'])}")
    lines.append(f"- content diffs: {len(report['content_diff'])}")
    lines.append("")

    lines.append("## Diff category counts")
    for key in ("tool_mapping_only", "metadata_only", "mixed", "substantial"):
        lines.append(f"- {CATEGORY_LABELS[key]}: {len(report['category_buckets'].get(key, []))}")
    lines.append("")

    lines.append("## Unallowlisted drift")
    lines.append(f"- missing in codex: {len(unallowlisted['missing_in_codex'])}")
    lines.append(f"- extra in codex: {len(unallowlisted['extra_in_codex'])}")
    lines.append(f"- content diffs: {len(unallowlisted['content_diff'])}")
    lines.append("")

    for key, title in (
        ("missing_in_codex", "Missing in codex"),
        ("extra_in_codex", "Extra in codex"),
        ("content_diff", "Content differences"),
    ):
        lines.append(f"## {title}")
        if not report[key]:
            lines.append("- none")
        else:
            for item in report[key]:
                marker = "(allowlisted)" if item in set(allowlist.get(key, [])) else ""
                lines.append(f"- `{item}` {marker}".rstrip())
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Report base-vs-codex skill drift")
    parser.add_argument("--base-root", default=str(DEFAULT_BASE_ROOT))
    parser.add_argument("--codex-root", default=str(DEFAULT_CODEX_ROOT))
    parser.add_argument("--allowlist", default=str(DEFAULT_ALLOWLIST))
    parser.add_argument("--json-out", default="")
    parser.add_argument("--markdown-out", default="")
    parser.add_argument("--priority-out", default="", help="Write convergence priority markdown report")
    parser.add_argument("--check", action="store_true", help="Exit non-zero if unallowlisted drift exists")
    args = parser.parse_args()

    report = compute_drift(Path(args.base_root), Path(args.codex_root))
    allowlist = load_allowlist(Path(args.allowlist))

    unallowlisted = {
        "missing_in_codex": subtract_allowlist(report["missing_in_codex"], allowlist["missing_in_codex"]),
        "extra_in_codex": subtract_allowlist(report["extra_in_codex"], allowlist["extra_in_codex"]),
        "content_diff": subtract_allowlist(report["content_diff"], allowlist["content_diff"]),
    }

    payload = {
        "report": report,
        "allowlist": allowlist,
        "unallowlisted": unallowlisted,
    }

    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    markdown = render_markdown(report, allowlist, unallowlisted)
    if args.markdown_out:
        out = Path(args.markdown_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(markdown, encoding="utf-8")

    priority_markdown = render_priority_markdown(report)
    if args.priority_out:
        out = Path(args.priority_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(priority_markdown, encoding="utf-8")

    print(
        "drift summary: "
        f"missing={len(report['missing_in_codex'])}, "
        f"extra={len(report['extra_in_codex'])}, "
        f"content_diff={len(report['content_diff'])}; "
        f"unallowlisted={len(unallowlisted['missing_in_codex']) + len(unallowlisted['extra_in_codex']) + len(unallowlisted['content_diff'])}"
    )

    if args.check:
        has_unallowlisted = any(unallowlisted[key] for key in unallowlisted)
        if has_unallowlisted:
            print("unallowlisted drift detected", file=sys.stderr)
            raise SystemExit(1)


if __name__ == "__main__":
    main()
