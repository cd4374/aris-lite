#!/usr/bin/env python3
"""Shared transforms for generated skill variant overlays."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)
SPAWN_BLOCK_RE = re.compile(r"```(?:yaml|text)?\nspawn_agent:\n([\s\S]*?)```")
SEND_BLOCK_RE = re.compile(r"```(?:yaml|text)?\nsend_input:\n([\s\S]*?)```")


@dataclass(frozen=True)
class TransformProfile:
    name: str
    override_note: str
    reviewer_line: str
    prereq_block: str
    review_start_tool: str
    review_reply_start_tool: str
    review_status_tool: str
    backend_name: str


def _claude_profile() -> TransformProfile:
    return TransformProfile(
        name="claude_review",
        override_note=(
            "> Override for Codex users who want **Claude Code**, not a second Codex agent, "
            "to act as the reviewer. Install this package **after** `skills/skills-codex/*`."
        ),
        reviewer_line=(
            "- **REVIEWER_MODEL = `claude-review`** — Claude reviewer invoked through the "
            "local `claude-review` MCP bridge. Set `CLAUDE_REVIEW_MODEL` if you need a "
            "specific Claude model override."
        ),
        prereq_block="""## Prerequisites

- Install the base Codex-native skills first: copy `skills/skills-codex/*` into `~/.codex/skills/`.
- Then install this overlay package: copy `skills/skills-codex-claude-review/*` into `~/.codex/skills/` and allow it to overwrite the same skill names.
- Register the local reviewer bridge:
  ```bash
  codex mcp add claude-review -- python3 ~/.codex/mcp-servers/claude-review/server.py
  ```
- This gives Codex access to `mcp__claude-review__review_start`, `mcp__claude-review__review_reply_start`, and `mcp__claude-review__review_status`.
""".strip(),
        review_start_tool="mcp__claude-review__review_start",
        review_reply_start_tool="mcp__claude-review__review_reply_start",
        review_status_tool="mcp__claude-review__review_status",
        backend_name="Claude",
    )


def _gemini_profile() -> TransformProfile:
    return TransformProfile(
        name="gemini_review",
        override_note=(
            "> Override for Codex users who want **Gemini**, not a second Codex agent, "
            "to act as the reviewer. Install this package **after** `skills/skills-codex/*`."
        ),
        reviewer_line=(
            "- **REVIEWER_MODEL = `gemini-review`** — Gemini reviewer invoked through the "
            "local `gemini-review` MCP bridge. Set `GEMINI_REVIEW_MODEL` if you need a "
            "specific Gemini model override."
        ),
        prereq_block="""## Prerequisites

- Install the base Codex-native skills first: copy `skills/skills-codex/*` into `~/.codex/skills/`.
- Then install this overlay package: copy `skills/skills-codex-gemini-review/*` into `~/.codex/skills/` and allow it to overwrite the same skill names.
- Register the local reviewer bridge:
  ```bash
  codex mcp add gemini-review -- python3 ~/.codex/mcp-servers/gemini-review/server.py
  ```
- This gives Codex access to `mcp__gemini-review__review_start`, `mcp__gemini-review__review_reply_start`, and `mcp__gemini-review__review_status`.
""".strip(),
        review_start_tool="mcp__gemini-review__review_start",
        review_reply_start_tool="mcp__gemini-review__review_reply_start",
        review_status_tool="mcp__gemini-review__review_status",
        backend_name="Gemini",
    )


TRANSFORM_PROFILES = {
    "claude_review": _claude_profile(),
    "gemini_review": _gemini_profile(),
}


def extract_field(frontmatter: str, field: str) -> str:
    pattern = re.compile(rf"^{re.escape(field)}:\s*(.+)$", re.MULTILINE)
    match = pattern.search(frontmatter)
    if not match:
        return ""
    value = match.group(1).strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        try:
            value = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            value = value[1:-1]
    return value


def build_frontmatter(name: str, description: str) -> str:
    safe_desc = description.replace('"', '\\"')
    return f'---\nname: "{name}"\ndescription: "{safe_desc}"\n---\n\n'


def normalize_description(text: str, profile: TransformProfile) -> str:
    fallback = f"{profile.backend_name}-review override for a Codex-native ARIS skill."
    text = text or fallback
    text = text.replace("GPT using a secondary Codex agent", f"{profile.backend_name} via {profile.name.replace('_', '-')} MCP")
    text = text.replace("using a secondary Codex agent", f"using {profile.backend_name} via {profile.name.replace('_', '-')} MCP")
    text = text.replace("via GPT-5.4 xhigh review", f"via {profile.backend_name} review through {profile.name.replace('_', '-')} MCP")
    return text


def _rewrite_spawn_block(match: re.Match[str], profile: TransformProfile) -> str:
    lines = match.group(1).splitlines()
    out = ["```", f"{profile.review_start_tool}:"]
    for line in lines:
        stripped = line.strip()
        if not stripped:
            out.append(line)
            continue
        if stripped.startswith("model:") or stripped.startswith("reasoning_effort:"):
            continue
        if stripped.startswith("message:"):
            out.append(line.replace("message:", "prompt:", 1))
            continue
        out.append(line)
    out.append("```")
    return "\n".join(out)


def _rewrite_send_block(match: re.Match[str], profile: TransformProfile) -> str:
    lines = match.group(1).splitlines()
    out = ["```", f"{profile.review_reply_start_tool}:"]
    for line in lines:
        stripped = line.strip()
        if not stripped:
            out.append(line)
            continue
        if stripped.startswith("model:") or stripped.startswith("reasoning_effort:"):
            continue
        if stripped.startswith("id:"):
            out.append(line.replace("id:", "threadId:", 1))
            continue
        if stripped.startswith("message:"):
            out.append(line.replace("message:", "prompt:", 1))
            continue
        out.append(line)
    out.append("```")
    return "\n".join(out)


def _append_async_notes(text: str, profile: TransformProfile) -> str:
    note = (
        "After this start call, immediately save the returned `jobId` and poll "
        f"`{profile.review_status_tool}` with a bounded `waitSeconds` until "
        "`done=true`. Treat the completed status payload's `response` as the "
        "reviewer output, and save the completed `threadId` for any follow-up round."
    )

    def repl(match: re.Match[str]) -> str:
        block = match.group(0)
        if note in block:
            return block
        return f"{block}\n\n{note}"

    return re.sub(
        rf"```(?:yaml|text)?\n(?:{re.escape(profile.review_start_tool)}:|{re.escape(profile.review_reply_start_tool)}:)[\s\S]*?```",
        repl,
        text,
    )


def transform_body(text: str, profile: TransformProfile) -> str:
    bridge = profile.name.replace("_", "-")
    review_name = profile.backend_name

    replacements = [
        ("secondary Codex agent", f"{review_name} reviewer via `{bridge}` MCP"),
        ("secondary Codex agent (xhigh reasoning)", f"{review_name} reviewer via `{bridge}` MCP"),
        ("GPT-5.4 xhigh", f"{review_name} review"),
        ("Send the full paper text to GPT-5.4 xhigh:", f"Send the full paper text to {review_name} through `{bridge}`:"),
        ("Send the complete outline to GPT-5.4 xhigh for feedback:", f"Send the complete outline to {review_name} for feedback:"),
        ("Send a detailed prompt with xhigh reasoning:", "Send a detailed prompt with high-rigor review:"),
        ("GPT-5.4 responses", f"{review_name} reviewer responses"),
        ("`agent_id`", "`thread_id`"),
        ('"agent_id"', '"thread_id"'),
        ("mcp__codex__codex", profile.review_start_tool),
        ("mcp__codex__codex-reply", profile.review_reply_start_tool),
    ]
    for old, new in replacements:
        text = text.replace(old, new)

    text = text.replace(
        "Call REVIEWER_MODEL via `spawn_agent` (`spawn_agent`) with xhigh reasoning:",
        f"Call REVIEWER_MODEL via `{profile.review_start_tool}` with high-rigor review:",
    )
    text = text.replace(
        "Use `send_input` with the returned agent id to continue the conversation:",
        f"Use `{profile.review_reply_start_tool}` with the saved completed `threadId`, then poll `{profile.review_status_tool}` with the returned `jobId` until `done=true` to continue the conversation:",
    )
    text = text.replace(
        "If this is round 2+, use `send_input` with the saved agent id to maintain continuity.",
        f"If this is round 2+, use `{profile.review_reply_start_tool}` with the saved completed `threadId`, then poll `{profile.review_status_tool}` with the returned `jobId` until `done=true` to maintain continuity.",
    )
    text = text.replace(
        "Save the agent id for Round 2.",
        f"Save the returned `jobId`, poll `{profile.review_status_tool}` until `done=true`, then save the completed `threadId` for Round 2.",
    )
    text = text.replace(
        "Save agent id from first call, use `send_input` for subsequent rounds",
        f"Save the completed `threadId` from the first `{profile.review_status_tool}` result, then use `{profile.review_reply_start_tool}` plus `{profile.review_status_tool}` for subsequent rounds",
    )
    text = text.replace("Document the agent id for potential future resumption", "Document the completed `threadId` for potential future resumption")
    text = text.replace(
        "Use `send_input` with the saved agent id:",
        f"Use `{profile.review_reply_start_tool}` with the saved completed `threadId`:",
    )
    text = text.replace(
        "use `send_input` for Round 2 to maintain conversation context",
        f"use `{profile.review_reply_start_tool}` plus `{profile.review_status_tool}` for Round 2 to maintain conversation context",
    )
    text = text.replace(
        "**CRITICAL: Save the `agent_id`** from this call for all later rounds.",
        f"**CRITICAL: Save the returned `jobId`**, poll `{profile.review_status_tool}` until `done=true`, then save the completed `threadId` from the status result for all later rounds.",
    )
    text = text.replace(
        "- **ALWAYS use `reasoning_effort: xhigh`** for all Codex review calls.",
        f"- **Always ask the {review_name} reviewer for strict, high-rigor feedback** in every review round.",
    )
    text = text.replace(
        "- **Save `agent_id` from Phase 2** and use `send_input` for later rounds.",
        f"- **Save the completed `threadId` from Phase 2** and use `{profile.review_reply_start_tool}` plus `{profile.review_status_tool}` for later rounds.",
    )
    text = text.replace(
        "- **Use `send_input`** for Round 2 to maintain conversation context",
        f"- **Use `{profile.review_reply_start_tool}` plus `{profile.review_status_tool}`** for Round 2 to maintain conversation context",
    )
    text = text.replace(
        "ALWAYS use `reasoning_effort: xhigh` for reviews",
        f"Always ask the {review_name} reviewer for strict, high-rigor feedback.",
    )
    text = text.replace(
        "ALWAYS use `reasoning_effort: xhigh` for maximum reasoning depth",
        f"Always ask the {review_name} reviewer for strict, high-rigor feedback.",
    )

    text = re.sub(r"^-\s+\*{0,2}REVIEWER_MODEL.*$", profile.reviewer_line, text, flags=re.MULTILINE)
    text = re.sub(r"## Prerequisites\n\n(?:- .*\n)+", profile.prereq_block + "\n\n", text, count=1)

    text = SPAWN_BLOCK_RE.sub(lambda m: _rewrite_spawn_block(m, profile), text)
    text = SEND_BLOCK_RE.sub(lambda m: _rewrite_send_block(m, profile), text)

    text = text.replace(
        "```\nreasoning_effort: xhigh\n```",
        f"```\n{profile.review_start_tool}:\n  prompt: |\n    [Full novelty briefing + prior work list + specific novelty questions]\n```",
    )

    return _append_async_notes(text, profile)


def generate_overlay_content(source_content: str, profile: TransformProfile, skill_name: str) -> str:
    match = FRONTMATTER_RE.match(source_content)
    if not match:
        raise ValueError(f"Missing frontmatter: {skill_name}")

    frontmatter = match.group(1)
    body = source_content[match.end():].lstrip("\n")
    name = extract_field(frontmatter, "name") or skill_name
    description = normalize_description(extract_field(frontmatter, "description"), profile)

    output = build_frontmatter(name, description)
    output += profile.override_note + "\n\n"
    output += transform_body(body, profile).rstrip() + "\n"
    return output
