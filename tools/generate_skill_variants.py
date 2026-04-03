#!/usr/bin/env python3
"""Generate/check skill variant overlays from a single manifest."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from skill_variant_transforms import TRANSFORM_PROFILES, generate_overlay_content


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "tools" / "skill_variants_manifest.yaml"


class DriftError(RuntimeError):
    pass


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "variants" not in data:
        raise ValueError("Invalid manifest: expected top-level object with 'variants'")
    return data


def iter_variants(manifest: dict, selected: list[str] | None = None) -> list[tuple[str, dict]]:
    variants = manifest.get("variants", {})
    if not isinstance(variants, dict):
        raise ValueError("Invalid manifest: 'variants' must be an object")

    names = selected or list(variants.keys())
    result: list[tuple[str, dict]] = []
    for name in names:
        if name not in variants:
            raise ValueError(f"Unknown variant: {name}")
        cfg = variants[name]
        if not isinstance(cfg, dict):
            raise ValueError(f"Invalid variant config: {name}")
        result.append((name, cfg))
    return result


def generate_variant(repo_root: Path, name: str, cfg: dict, write: bool) -> list[str]:
    source_root = repo_root / cfg["source_root"]
    target_root = repo_root / cfg["target_root"]
    profile_name = cfg["transform_profile"]
    targets = cfg["targets"]

    if profile_name not in TRANSFORM_PROFILES:
        raise ValueError(f"Unknown transform_profile '{profile_name}' for variant {name}")
    profile = TRANSFORM_PROFILES[profile_name]

    drift: list[str] = []

    for skill_name in targets:
        src_path = source_root / skill_name / "SKILL.md"
        dst_dir = target_root / skill_name
        dst_path = dst_dir / "SKILL.md"

        if not src_path.exists():
            raise FileNotFoundError(f"Missing source skill: {src_path}")

        source_content = src_path.read_text(encoding="utf-8")
        expected = generate_overlay_content(source_content, profile, skill_name)

        current = dst_path.read_text(encoding="utf-8") if dst_path.exists() else None
        if current != expected:
            drift.append(f"{name}: {dst_path.relative_to(repo_root)}")
            if write:
                if dst_dir.exists():
                    shutil.rmtree(dst_dir)
                dst_dir.mkdir(parents=True, exist_ok=True)
                dst_path.write_text(expected, encoding="utf-8")

    return drift


def run_check(repo_root: Path, selected_variants: list[str] | None = None, write: bool = False) -> list[str]:
    manifest = load_manifest()
    variants = iter_variants(manifest, selected_variants)

    all_drift: list[str] = []
    for name, cfg in variants:
        drift = generate_variant(repo_root, name, cfg, write=write)
        all_drift.extend(drift)
    return all_drift


def list_variants(manifest: dict) -> str:
    lines: list[str] = []
    for name, cfg in manifest.get("variants", {}).items():
        lines.append(f"- {name}")
        lines.append(f"  source: {cfg['source_root']}")
        lines.append(f"  target: {cfg['target_root']}")
        lines.append(f"  profile: {cfg['transform_profile']}")
        lines.append(f"  skills: {len(cfg['targets'])}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate/check skill variant overlays")
    parser.add_argument("--variant", action="append", dest="variants", help="Variant name (repeatable)")
    parser.add_argument("--write", action="store_true", help="Write generated outputs")
    parser.add_argument("--check", action="store_true", help="Fail if drift is found")
    parser.add_argument("--list", action="store_true", help="List configured variants")
    args = parser.parse_args()

    manifest = load_manifest()

    if args.list:
        print(list_variants(manifest))
        return

    drift = run_check(REPO_ROOT, selected_variants=args.variants, write=args.write)

    if args.write:
        if drift:
            print(f"updated {len(drift)} file(s)")
        else:
            print("no changes")

    if args.check:
        if drift:
            print("drift detected:")
            for entry in drift:
                print(f"  {entry}")
            raise DriftError(f"Found {len(drift)} drifted generated file(s)")
        print("ok: no drift")


if __name__ == "__main__":
    try:
        main()
    except DriftError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
