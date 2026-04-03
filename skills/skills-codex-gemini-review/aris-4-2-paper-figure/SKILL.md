---
name: "aris-4-2-paper-figure"
description: "Generate publication-quality figures and tables from experiment results. Use when user says \"画图\", \"作图\", \"generate figures\", \"paper figures\", or needs plots for a paper."
---

> Override for Codex users who want **Gemini**, not a second Codex agent, to act as the reviewer. Install this package **after** `skills/skills-codex/*`.

# Paper Figure: Publication-Quality Plots from Experiment Data

Generate all figures and tables for a paper based on: **$ARGUMENTS**

## Scope: What This Skill Can and Cannot Do

| Category | Can auto-generate? | Examples |
|----------|-------------------|----------|
| **Data-driven plots** | ✅ Yes | Line plots (training curves), bar charts (method comparison), scatter plots, heatmaps, box/violin plots |
| **Comparison tables** | ✅ Yes | LaTeX tables comparing prior bounds, method features, ablation results |
| **Multi-panel figures** | ✅ Yes | Subfigure grids combining multiple plots (e.g., 3×3 dataset × method) |
| **Architecture/pipeline diagrams** | ❌ No — manual | Model architecture, data flow diagrams, system overviews. At best can generate a rough TikZ skeleton, but **expect to draw these yourself** using tools like draw.io, Figma, or TikZ |
| **Generated image grids** | ❌ No — manual | Grids of generated samples (e.g., GAN/diffusion outputs). These come from running your model, not from this skill |
| **Photographs / screenshots** | ❌ No — manual | Real-world images, UI screenshots, qualitative examples |

**In practice:** For a typical ML paper, this skill handles ~60% of figures (all data plots + tables). The remaining ~40% (hero figure, architecture diagram, qualitative results) need to be created manually and placed in `figures/` before running `/aris-4-4-paper-write`. The skill will detect these as "existing figures" and preserve them.

## Constants

- **STYLE = `publication`** — Visual style preset. Options: `publication` (default, clean for print), `poster` (larger fonts), `slide` (bold colors)
- **DPI = 300** — Output resolution
- **FORMAT = `pdf`** — Output format. Options: `pdf` (vector, best for LaTeX), `png` (raster fallback)
- **COLOR_PALETTE = `tab10`** — Default matplotlib color cycle. Options: `tab10`, `Set2`, `colorblind` (deuteranopia-safe)
- **FONT_SIZE = 10** — Base font size (matches typical conference body text)
- **FIG_DIR = `figures/`** — Output directory for generated figures
- **REVIEWER_MODEL = `gemini-review`** — Gemini reviewer invoked through the local `gemini-review` MCP bridge. Set `GEMINI_REVIEW_MODEL` if you need a specific Gemini model override.
- **MAX_ROUNDS = 2** — Maximum review→fix→re-review rounds.
- **FIGURE_ISSUE_LEDGER = `figures/FIGURE_ISSUE_LEDGER.md`** — Issue closure ledger for figures.
- **CLOSURE_REQUIRED = true** — Do not stop on score alone if major figure-quality issues remain open.

## Inputs

1. **`05_PAPER_PLAN.md`** (preferred) or `PAPER_PLAN.md` — figure plan table (from `/aris-4-1-paper-plan`)
2. **Experiment data** — JSON files, CSV files, or screen logs in `figures/` or project root
3. **Existing figures** — any manually created figures to preserve

If no canonical/legacy paper plan exists, scan for data files and ask the user which figures to generate.

## Workflow

### Step 1: Read Figure Plan

Parse the Figure Plan table from `05_PAPER_PLAN.md` first (fallback: `PAPER_PLAN.md`):

```markdown
| ID | Type | Description | Data Source | Priority |
|----|------|-------------|-------------|----------|
| Fig 1 | Architecture | ... | manual | HIGH |
| Fig 2 | Line plot | ... | figures/exp.json | HIGH |
```

Identify:
- Which figures can be auto-generated from data
- Which need manual creation (architecture diagrams, etc.)
- Which are comparison tables (generate as LaTeX)
- Which manual figures need placeholder/manifest tracking in `05_FIGURE_MANIFEST.md`

### Step 2: Set Up Plotting Environment

Create a shared style configuration script:

```python
# paper_plot_style.py — shared across all figure scripts
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams.update({
    'font.size': FONT_SIZE,
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'Times', 'DejaVu Serif'],
    'axes.labelsize': FONT_SIZE,
    'axes.titlesize': FONT_SIZE + 1,
    'xtick.labelsize': FONT_SIZE - 1,
    'ytick.labelsize': FONT_SIZE - 1,
    'legend.fontsize': FONT_SIZE - 1,
    'figure.dpi': DPI,
    'savefig.dpi': DPI,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
    'axes.grid': False,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'text.usetex': False,  # set True if LaTeX is available
    'mathtext.fontset': 'stix',
})

# Color palette
COLORS = plt.cm.tab10.colors  # or Set2, or colorblind-safe

def save_fig(fig, name, fmt=FORMAT):
    """Save figure to FIG_DIR with consistent naming."""
    fig.savefig(f'{FIG_DIR}/{name}.{fmt}')
    print(f'Saved: {FIG_DIR}/{name}.{fmt}')
```

### Step 3: Auto-Select Figure Type

Use this decision tree for data-driven figures (inspired by Imbad0202/academic-research-skills):

| Data Pattern | Recommended Type | Size |
|-------------|-----------------|------|
| X=time/steps, Y=metric | Line plot | 0.48\textwidth |
| Methods × 1 metric | Bar chart | 0.48\textwidth |
| Methods × multiple metrics | Grouped bar / radar | 0.95\textwidth |
| Two continuous variables | Scatter plot | 0.48\textwidth |
| Matrix / grid values | Heatmap | 0.48\textwidth |
| Distribution comparison | Box/violin plot | 0.48\textwidth |
| Multi-dataset results | Multi-panel (subfigure) | 0.95\textwidth |
| Prior work comparison | LaTeX table | — |

### Step 4: Generate Each Figure

For each figure in the plan, create a standalone Python script:

**Line plots** (training curves, scaling):
```python
# gen_fig2_training_curves.py
from paper_plot_style import *
import json

with open('figures/exp_results.json') as f:
    data = json.load(f)

fig, ax = plt.subplots(1, 1, figsize=(5, 3.5))
ax.plot(data['steps'], data['fac_loss'], label='Factorized', color=COLORS[0])
ax.plot(data['steps'], data['crf_loss'], label='CRF-LR', color=COLORS[1])
ax.set_xlabel('Training Steps')
ax.set_ylabel('Cross-Entropy Loss')
ax.legend(frameon=False)
save_fig(fig, 'fig2_training_curves')
```

**Bar charts** (comparison, ablation):
```python
fig, ax = plt.subplots(1, 1, figsize=(5, 3))
methods = ['Baseline', 'Method A', 'Method B', 'Ours']
values = [82.3, 85.1, 86.7, 89.2]
bars = ax.bar(methods, values, color=[COLORS[i] for i in range(len(methods))])
ax.set_ylabel('Accuracy (%)')
# Add value labels on bars
for bar, val in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f'{val:.1f}', ha='center', va='bottom', fontsize=FONT_SIZE-1)
save_fig(fig, 'fig3_comparison')
```

**Comparison tables** (LaTeX, for theory papers):
```latex
\begin{table}[t]
\centering
\caption{Comparison of estimation error bounds. $n$: sample size, $D$: ambient dim, $d$: latent dim, $K$: subspaces, $n_k$: modes.}
\label{tab:bounds}
\begin{tabular}{lccc}
\toprule
Method & Rate & Depends on $D$? & Multi-modal? \\
\midrule
\citet{MinimaxOkoAS23} & $n^{-s'/D}$ & Yes (curse) & No \\
\citet{ScoreMatchingdistributionrecovery} & $n^{-2/d}$ & No & No \\
\textbf{Ours} & $\sqrt{\sum n_k d_k / n}$ & No & Yes \\
\bottomrule
\end{tabular}
\end{table}
```

**Architecture/pipeline diagrams** (MANUAL — outside this skill's scope):
- These require manual creation using draw.io, Figma, Keynote, or TikZ
- This skill can generate a rough TikZ skeleton as a starting point, but **do not expect publication-quality results**
- If the figure already exists in `figures/`, preserve it and generate only the LaTeX `\includegraphics` snippet
- Flag as `[MANUAL]` in the figure plan and `latex_includes.tex`
- Record each unresolved manual figure in `05_FIGURE_MANIFEST.md` with status such as `manual-required`, `manual-placeholder`, `manual-existing`, or `missing`

### Step 5: Run All Scripts

```bash
# Run all figure generation scripts
for script in gen_fig*.py; do
    python "$script"
done
```

Verify all output files exist and are non-empty.

### Step 6: Generate LaTeX Include Snippets

For each figure, output the LaTeX code to include it:

```latex
% === Fig 2: Training Curves ===
\begin{figure}[t]
    \centering
    \includegraphics[width=0.48\textwidth]{figures/fig2_training_curves.pdf}
    \caption{Training curves comparing factorized and CRF-LR denoising.}
    \label{fig:training_curves}
\end{figure}
```

Save all snippets to `figures/latex_includes.tex` for easy copy-paste into the paper. If a manual figure is unresolved, emit a clearly marked placeholder include/snippet and capture the blocker in `05_FIGURE_MANIFEST.md`.

### Step 7: Figure Quality Review Loop

Iterate review → fix → re-review until figures pass quality gate or MAX_ROUNDS reached.

#### Round 1 Review

Send figure descriptions and captions to GPT-5.4 for review:

```
mcp__gemini-review__review_start:
  model: gpt-5.4
  config: {"model_reasoning_effort": "xhigh"}
  prompt: |
    Review these figure/table plans for a [VENUE] submission.

    For each figure:
    1. Is the caption informative and self-contained?
    2. Does the figure type match the data being shown?
    3. Is the comparison fair and clear?
    4. Which claim ID does this figure support?
    5. Is the comparison sufficient to support that claim?
    6. Does the caption overstate beyond the evidence shown?
    7. Any missing baselines or ablations?
    8. Would a different visualization be more effective?
    9. Are there visual quality issues (fonts, colors, labels, legend)?
    10. Is the figure print-ready (grayscale-safe, proper sizing)?

    Also provide:
    - **Overall Figure Quality Score** (1-10)
    - **CRITICAL issues** (claim misalignment, missing comparison, severe visual flaw)
    - **MAJOR issues** (caption weakness, minor visual problems)
    - **MINOR issues** (polish suggestions)
    - **Must-fix-before-next-round items**
    - **Verdict**: Ready for paper? Yes / Almost / No

    [list all figures with captions and descriptions]
```

After this start call, immediately save the returned `jobId` and poll `mcp__gemini-review__review_status` with a bounded `waitSeconds` until `done=true`. Treat the completed status payload's `response` as the reviewer output, and save the completed `threadId` for any follow-up round.

Save the threadId for subsequent rounds.

#### Parse and Record Issues

Extract structured fields from the review:
- **Score** (1-10)
- **Verdict** (ready / almost / not ready)
- **Issues by figure** with severity

Create or update `FIGURE_ISSUE_LEDGER.md`:

```markdown
# Figure Issue Ledger

## Round 1 Issues

| Issue ID | Figure | Severity | Issue | Fix Planned | Status |
|----------|--------|----------|-------|-------------|--------|
| F1-1 | Fig 2 | CRITICAL | Missing baseline X | Add baseline | open |
| F1-2 | Fig 3 | MAJOR | Caption overclaims | Soften wording | open |

## Issue Status Delta
| Issue ID | Previous Status | Fix Applied | New Status |
|----------|-----------------|-------------|------------|
| ... | ... | ... | ... |
```

#### Implement Fixes

For each open issue:
1. Regenerate the affected figure with the fix
2. Update the LaTeX snippet if caption changed
3. Update the issue status in the ledger

Priority order:
1. CRITICAL fixes (claim misalignment, missing comparison)
2. MAJOR fixes (caption issues, visual quality)
3. MINOR fixes (polish)

#### Round 2+ Review (if needed)

Use `mcp__gemini-review__review_start-reply` with the saved threadId:

```
mcp__gemini-review__review_start-reply:
  threadId: [saved from Round 1]
  model: gpt-5.4
  config: {"model_reasoning_effort": "xhigh"}
  prompt: |
    [Round N update]

    Since your last review, we have fixed:
    1. [Fix 1]: [description]
    2. [Fix 2]: [description]

    Please re-score and re-assess. Same format:
    Score, Issues by severity, Must-fix items, Verdict.
```

Update the issue ledger with new status delta.

#### Stop Condition

Stop when:
- Score >= 7 AND verdict is "ready" AND no CRITICAL issues remain open
- OR MAX_ROUNDS reached

Do not stop on score alone if any CRITICAL figure issue remains open.

### Step 8: Final Figure Quality Report

After the review loop completes, write a summary:

```markdown
# Figure Generation Report

**Date**: [today]
**Rounds**: N / MAX_ROUNDS
**Final Score**: X / 10
**Final Verdict**: Ready / Almost / Not ready

## Score Progression
| Round | Score | Key Changes |
|-------|-------|-------------|
| Round 1 | X/10 | [summary of fixes] |
| Round 2 | Y/10 | [summary of fixes] |

## Issue Closure Summary
| Severity | Total | Closed | Remaining |
|----------|-------|--------|-----------|
| CRITICAL | X | Y | Z |
| MAJOR | X | Y | Z |
| MINOR | X | Y | Z |

## Remaining Issues
- [list of unresolved issues]

## Figures Generated
- [list of auto-generated figures]
- [list of manual figures tracked in manifest]
```

### Step 9: Quality Checklist

- [ ] Font size readable at printed paper size (not too small)
- [ ] Colors distinguishable in grayscale (print-friendly)
- [ ] **No title inside figures** — titles go only in LaTeX `\caption{}` (from pedrohcgs)
- [ ] Legend does not overlap data
- [ ] Axis labels have units where applicable
- [ ] Axis labels are publication-quality (not variable names like `emp_rate`)
- [ ] Figure width fits single column (0.48\textwidth) or full width (0.95\textwidth)
- [ ] PDF output is vector (not rasterized text)
- [ ] No matplotlib default title (remove `plt.title` for publications)
- [ ] Serif font matches paper body text (Times / Computer Modern)
- [ ] Colorblind-accessible (if using colorblind palette)
- [ ] Every figure has a linked claim ID
- [ ] Caption wording does not overclaim beyond shown evidence
- [ ] Hero figure is consistent with the strongest safe claim

## Output

```
figures/
├── paper_plot_style.py          # shared style config
├── gen_fig1_architecture.py     # per-figure scripts
├── gen_fig2_training_curves.py
├── gen_fig3_comparison.py
├── fig1_architecture.pdf        # generated figures
├── fig2_training_curves.pdf
├── fig3_comparison.pdf
├── latex_includes.tex           # LaTeX snippets for all figures
├── TABLE_*.tex                  # standalone table LaTeX files
├── FIGURE_ISSUE_LEDGER.md       # issue closure ledger
└── FIGURE_QUALITY_REPORT.md     # final quality report
```

## Key Rules

- **Every figure must be reproducible** — save the generation script alongside the output
- **Do NOT hardcode data** — always read from JSON/CSV files
- **Use vector format (PDF)** for all plots — PNG only as fallback
- **No decorative elements** — no background colors, no 3D effects, no chart junk
- **Consistent style across all figures** — same fonts, colors, line widths
- **Colorblind-safe** — verify with https://davidmathlogic.com/colorblind/ if needed
- **One script per figure** — easy to re-run individual figures when data changes
- **No titles inside figures** — captions are in LaTeX only
- **Comparison tables count as figures** — generate them as standalone .tex files
- **Manual figures must be tracked explicitly** — unresolved high-priority manual figures go into `05_FIGURE_MANIFEST.md`; do not just warn and move on without recording status
- **Figure issues integrate with paper improvement loop** — `FIGURE_ISSUE_LEDGER.md` should be inspected by `/aris-4-6-auto-paper-improvement-loop` and `/aris-4-8-submission-gate`
- **Closure matters more than score** — do not stop on score alone if CRITICAL figure issues remain open

## Integration with Paper Improvement Loop

The figure issue ledger (`FIGURE_ISSUE_LEDGER.md`) integrates with the main paper quality workflow:

1. **During `/aris-4-6-auto-paper-improvement-loop`**: The paper reviewer should also check for unresolved figure issues flagged in the ledger.

2. **During `/aris-4-8-submission-gate`**: The submission gate should verify:
   - No unresolved CRITICAL figure issues in the ledger
   - All HIGH-priority figures have been generated or explicitly marked as manual-existing
   - Figure quality report exists

3. **Cross-referencing**: Each figure's linked claim ID should match the Claims-Evidence Matrix in `05_PAPER_PLAN.md`.

## Figure Type Reference

| Type | When to Use | Typical Size |
|------|------------|--------------|
| Line plot | Training curves, scaling trends | 0.48\textwidth |
| Bar chart | Method comparison, ablation | 0.48\textwidth |
| Grouped bar | Multi-metric comparison | 0.95\textwidth |
| Scatter plot | Correlation analysis | 0.48\textwidth |
| Heatmap | Attention, confusion matrix | 0.48\textwidth |
| Box/violin | Distribution comparison | 0.48\textwidth |
| Architecture | System overview | 0.95\textwidth |
| Multi-panel | Combined results (subfigures) | 0.95\textwidth |
| Comparison table | Prior bounds vs. ours (theory) | full width |

## Acknowledgements

Design pattern (type × style matrix) inspired by [baoyu-skills](https://github.com/jimliu/baoyu-skills). Publication style defaults and figure rules from [pedrohcgs/claude-code-my-workflow](https://github.com/pedrohcgs/claude-code-my-workflow). Visualization decision tree from [Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills).
