---
name: "aris-1-5-novelty-check"
description: "Verify research idea novelty against recent literature. Use when user says \"查新\", \"novelty check\", \"有没有人做过\", \"check novelty\", or wants to verify a research idea is novel before implementing."
---

> Override for Codex users who want **Claude Code**, not a second Codex agent, to act as the reviewer. Install this package **after** `skills/skills-codex/*`.

# Novelty Check Skill

Check whether a proposed method/idea has already been done in the literature: **$ARGUMENTS**

## Constants

- **REVIEWER_MODEL = `claude-review`** — Claude reviewer invoked through the local `claude-review` MCP bridge. Set `CLAUDE_REVIEW_MODEL` if you need a specific Claude model override.
- MAX_SEARCH_ROUNDS = 3 — Maximum iterations of search → verify → refine
- NOVELTY_THRESHOLD = 7 — Ideas scoring < 7/10 require additional verification or refinement

## Instructions

Given a method description, systematically verify its novelty through iterative refinement:

### Phase A: Extract Key Claims
1. Read the user's method description
2. Identify 3-5 core technical claims that would need to be novel:
   - What is the method?
   - What problem does it solve?
   - What is the mechanism?
   - What makes it different from obvious baselines?

### Phase B: Multi-Source Literature Search
For EACH core claim, search using ALL available sources:

1. **Web Search** (via `WebSearch`):
   - Search arXiv, Google Scholar, Semantic Scholar
   - Use specific technical terms from the claim
   - Try at least 3 different query formulations per claim
   - Include year filters for 2024-2026

2. **Known paper databases**: Check against:
   - ICLR 2025/2026, NeurIPS 2025, ICML 2025/2026
   - Recent arXiv preprints (2025-2026)

3. **Read abstracts**: For each potentially overlapping paper, WebFetch its abstract and related work section

### Phase C: Cross-Model Verification
Call REVIEWER_MODEL via Codex MCP (`mcp__claude-review__review_start`) with xhigh reasoning:
```
config: {"model_reasoning_effort": "xhigh"}
```
Prompt should include:
- The proposed method description
- All papers found in Phase B
- Ask: "Is this method novel? What is the closest prior work? What is the delta?"

### Phase D: Novelty Report

Output a structured report:

```markdown
## Novelty Check Report

### Proposed Method
[1-2 sentence description]

### Core Claims
1. [Claim 1] — Novelty: HIGH/MEDIUM/LOW — Closest: [paper]
2. [Claim 2] — Novelty: HIGH/MEDIUM/LOW — Closest: [paper]
...

### Closest Prior Work
| Paper | Year | Venue | Overlap | Key Difference |
|-------|------|-------|---------|----------------|

### Overall Novelty Assessment
- Score: X/10
- Recommendation: PROCEED / PROCEED WITH CAUTION / ABANDON
- Key differentiator: [what makes this unique, if anything]
- Risk: [what a reviewer would cite as prior work]

### Suggested Positioning
[How to frame the contribution to maximize novelty perception]
```

### Phase E: Iterative Refinement (Autoresearch Pattern)

If novelty score < NOVELTY_THRESHOLD:

#### Round 1: Refine the Idea

1. **Identify the delta**: What specific aspect could be changed to increase novelty?
   - Different problem setting?
   - Different mechanism?
   - Different evaluation?

2. **Generate refined variants**:
```
mcp__claude-review__review_start-reply:
  threadId: [saved]
  prompt: |
    The novelty score was X/10, which is below threshold.

    Generate 2-3 REFINED variants of this idea that would score higher:

    1. Each variant should address a specific overlap issue
    2. Each variant should be testable with similar resources
    3. Explain why each variant would be more novel

    Original idea: [description]
    Overlap issues: [from Phase C]
```

3. **Quick-check refined variants**: For each variant, do a targeted search (2-3 queries) to see if it exists.

4. **Re-evaluate**: If a refined variant shows promise, run Phase C again with the variant.

#### Round 2+: Repeat Until Threshold Met or MAX_SEARCH_ROUNDS Reached

- Track search queries and results to avoid repeating
- Each round should focus on a different aspect (method, setting, evaluation)
- Document all variants tried and their outcomes

#### Final Report Update

Add to the novelty report:

```markdown
## Iterative Refinement Log

| Round | Variant | Search Queries | Result | Novelty Score |
|-------|---------|----------------|--------|---------------|
| 1 | Original | ... | Found overlap with X | 5/10 |
| 1 | Refined A | ... | No direct overlap | 7/10 |
| 2 | Refined A+ | ... | Confirmed novel | 8/10 |

## Recommended Variant
[Best-scoring variant or original if unrefined]

## Remaining Risks
[Even with refinement, what could a reviewer still object to?]
```

### Important Rules
- Be BRUTALLY honest — false novelty claims waste months of research time
- "Applying X to Y" is NOT novel unless the application reveals surprising insights
- Check both the method AND the experimental setting for novelty
- If the method is not novel but the FINDING would be, say so explicitly
- Always check the most recent 6 months of arXiv — the field moves fast
- **Iterate when score is low**: Don't stop at one negative result — refine and re-check
- **Document all variants**: Future searches should not repeat failed queries
