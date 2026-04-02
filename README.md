# aris-lite

> 本项目基于原项目 [wanshuiyin/Auto-claude-code-research-in-sleep](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) 改造。
>
> README 这里只保留**安装、用法、工作流、参数与集成配置**等和实际使用直接相关的内容；原项目的背景介绍、设计理念、效果展示、路线图、引用等说明请直接查看原项目。

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/cd4374/aris-lite.git
cd aris-lite

# 2. 安装 skills 到 Claude Code
cp -r skills/* ~/.claude/skills/

# 3. （仅 review 类 skill 需要）安装 Codex MCP
npm install -g @openai/codex
codex setup                    # 提示选模型时选 gpt-5.4
claude mcp add codex -s user -- codex mcp-server

# 4. 进入 Claude Code 使用
claude
```

常用命令：

```text
/aris-0-2-idea-discovery "你的研究方向"              # 工作流 1：idea 发现
/aris-0-3-experiment-bridge                         # 工作流 1.5：实现 + 部署 + 初始结果
/aris-3-1-auto-review-loop "你的论文主题或范围"         # 工作流 2：自动 review 循环
/aris-4-7-paper-writing "NARRATIVE_REPORT.md"       # 工作流 3：论文写作
/aris-5-1-rebuttal "paper/ + reviews" — venue: ICML  # 工作流 4：rebuttal
/aris-0-1-research-pipeline "你的研究方向"            # 全流程：1 → 1.5 → 2 → 3
```

模板见 [`templates/`](templates/)：
- [`RESEARCH_BRIEF_TEMPLATE.md`](templates/RESEARCH_BRIEF_TEMPLATE.md)
- [`EXPERIMENT_PLAN_TEMPLATE.md`](templates/EXPERIMENT_PLAN_TEMPLATE.md)
- [`NARRATIVE_REPORT_TEMPLATE.md`](templates/NARRATIVE_REPORT_TEMPLATE.md)
- [`PAPER_PLAN_TEMPLATE.md`](templates/PAPER_PLAN_TEMPLATE.md)

## 工作流导航

### 全流程（`aris-0-1-research-pipeline`）

适合：希望从研究方向直接串起 idea 发现、实验桥接、自动 review 和论文写作。

入口：

```text
/aris-0-1-research-pipeline "你的研究方向"
```

支持组合输入：

```text
/aris-0-1-research-pipeline "改进方法 X" — ref paper: https://arxiv.org/abs/2406.04329
/aris-0-1-research-pipeline "改进方法 X" — base repo: https://github.com/org/project
/aris-0-1-research-pipeline "改进方法 X" — ref paper: https://arxiv.org/abs/2406.04329, base repo: https://github.com/org/project
```

流程：

```text
工作流 1：idea 发现
→ 工作流 1.5：实验桥接
→ 工作流 2：自动 review 循环
→ 工作流 3：论文写作
```

常见用法：
- 只给研究方向：自动从调研到论文写作全流程推进
- 给 `ref paper`：先围绕参考论文总结和找改进点
- 给 `base repo`：基于现有代码仓库实现和部署实验
- 两者都给：围绕“这篇论文 + 这套代码”组织完整工作流

### 工作流 1：Idea 发现

适合：还没有具体 idea，只有研究方向。

入口：

```text
/aris-0-2-idea-discovery "你的研究方向"
```

典型流程：

```text
/aris-1-1-research-lit
→ /aris-1-4-idea-creator
→ /aris-1-5-novelty-check
→ /aris-1-6-research-review
→ /aris-1-7-research-refine
→ /aris-1-8-experiment-plan
```

主要输出：
- `IDEA_REPORT.md`
- `refine-logs/FINAL_PROPOSAL.md`
- `refine-logs/EXPERIMENT_PLAN.md`

### 工作流 1.5：实验桥接

适合：已经有实验计划，需要实现代码、做 sanity check、部署实验并收集初始结果。

入口：

```text
/aris-0-3-experiment-bridge
# 或
/aris-0-3-experiment-bridge "my_plan.md"
```

默认会读取：
- `refine-logs/EXPERIMENT_PLAN.md`

典型流程：

```text
解析实验计划
→ 实现实验代码
→ 代码审查（可选）
→ sanity check
→ 部署到 GPU / 本地环境
→ 收集初始结果
```

### 工作流 2：自动 Review 循环

适合：已有实验结果或论文草稿，需要自动 review → 修复 → 再 review。

入口：

```text
/aris-3-1-auto-review-loop "你的论文主题或范围"
```

也支持：

```text
/aris-3-1-auto-review-loop
```

该 skill 会自动读取项目中的叙事文档、实验结果和历史 review 上下文。

### 工作流 3：论文写作

适合：已有 `NARRATIVE_REPORT.md`，希望生成投稿论文。

入口：

```text
/aris-4-7-paper-writing "NARRATIVE_REPORT.md"
```

分步模式：

```text
/aris-4-1-paper-plan
→ /aris-4-2-paper-figure
→ /aris-4-4-paper-write
→ /aris-4-5-paper-compile
→ /aris-4-6-auto-paper-improvement-loop
```

输入建议：
- 研究问题
- 关键声明
- 实验设置
- 定量结果
- 图表说明

### 工作流 4：Rebuttal

适合：已经收到审稿意见，需要生成 rebuttal 草稿。

入口：

```text
/aris-5-1-rebuttal "paper/ + reviews" — venue: ICML, character limit: 5000
```

主要参数：
- `venue`：目标会议
- `character limit`：必填，回复字数限制
- `quick mode`：只做解析和策略
- `auto experiment`：自动补实验
- `max stress test rounds`
- `max followup rounds`

输出：
- `PASTE_READY.txt`
- `REBUTTAL_DRAFT_rich.md`

## 常用参数

所有流水线命令都支持内联参数：

```text
/aris-0-1-research-pipeline "你的课题" — AUTO_PROCEED: false
/aris-0-1-research-pipeline "你的课题" — human checkpoint: true
/aris-0-1-research-pipeline "你的课题" — sources: zotero, web
/aris-0-1-research-pipeline "你的课题" — arxiv download: true
```

常用参数如下：

| 参数 | 默认值 | 作用 |
|------|--------|------|
| `AUTO_PROCEED` | `true` | idea 选择阶段自动继续 |
| `human checkpoint` | `false` | 每轮 review 后暂停等待人工确认 |
| `sources` | `all` | 文献源：`zotero`、`obsidian`、`local`、`web`、`semantic-scholar`、`all` |
| `arxiv download` | `false` | 下载最相关的 arXiv PDF |
| `DBLP_BIBTEX` | `true` | 用 DBLP/CrossRef 获取真实 BibTeX |
| `code review` | `true` | 部署前进行代码审查 |
| `wandb` | `false` | 自动注入 W&B 日志 |
| `illustration` | `gemini` | AI 作图：`gemini`、`mermaid`、`false` |
| `venue` | `ICLR` | 目标会议 / 期刊模板 |
| `base repo` | `false` | 基础代码仓库 URL |
| `compact` | `false` | 生成精简摘要文件 |
| `ref paper` | `false` | 参考论文 PDF 路径或 arXiv URL |

## 安装

### 前置条件

1. 安装 [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
2. （仅 review 类 skill 需要）安装 [Codex CLI](https://github.com/openai/codex) 并配置为 MCP server：

```bash
npm install -g @openai/codex
claude mcp add codex -s user -- codex mcp-server
```

3. （仅工作流 3：论文写作需要）安装 LaTeX 环境，至少包含 `latexmk` 和 `pdfinfo`：

```bash
# macOS
brew install --cask mactex    # 或 brew install basictex
brew install poppler

# Ubuntu/Debian
sudo apt install texlive-full latexmk poppler-utils

# 验证
latexmk --version && pdfinfo -v
```

### 安装 Skills

```bash
git clone https://github.com/cd4374/aris-lite.git
cd aris-lite

# 安装全部 skills
cp -r skills/* ~/.claude/skills/

# 或只安装指定 skill
cp -r skills/aris-3-1-auto-review-loop ~/.claude/skills/
cp -r skills/aris-1-1-research-lit ~/.claude/skills/
```

### 更新 Skills

```bash
cd aris-lite
git pull

# 全量更新
cp -r skills/* ~/.claude/skills/

# 安全更新（只新增，不覆盖本地已改内容）
cp -rn skills/* ~/.claude/skills/

# 只更新单个 skill
cp -r skills/aris-0-3-experiment-bridge ~/.claude/skills/
```

### 免确认配置（可选）

在 `.claude/settings.local.json` 中添加：

```json
{
  "permissions": {
    "allow": [
      "mcp__codex__codex",
      "mcp__codex__codex-reply",
      "Write",
      "Edit",
      "Skill(auto-review-loop)"
    ]
  }
}
```

## 可选集成

### GPU 服务器配置

如果需要自动部署实验，在项目 `CLAUDE.md` 中添加你的服务器信息：

```markdown
## 远程服务器

- SSH：`ssh my-gpu-server`
- GPU：4x A100
- Conda 环境：`research`
- 激活：`eval "$(/opt/conda/bin/conda shell.bash hook)" && conda activate research`
- 代码目录：`/home/user/experiments/`
- 后台运行：`screen -dmS exp0 bash -c '...'`
```

如果当前机器本身就有 GPU，也可以直接描述本机环境。

### Zotero 集成（可选）

```bash
uv tool install zotero-mcp-server
claude mcp add zotero -s user -- zotero-mcp -e ZOTERO_LOCAL=true
```

或使用 Web API：

```bash
claude mcp add zotero -s user -- zotero-mcp \
  -e ZOTERO_API_KEY=your_key -e ZOTERO_USER_ID=your_id
```

用于：
- 搜索 Zotero 文献库
- 读取 PDF 标注
- 导出 BibTeX

### Obsidian 集成（可选）

```bash
claude mcp add obsidian-vault -s user -- npx @bitbonsai/mcpvault@latest /path/to/your/vault
```

用于：
- 搜索研究笔记
- 沿标签 / wikilinks 查找相关内容
- 将个人笔记纳入文献调研上下文

### arXiv 集成

`/aris-1-1-research-lit` 默认使用 arXiv API 获取元数据。

下载 PDF：

```text
/aris-1-1-research-lit "topic" — arxiv download: true
/aris-1-1-research-lit "topic" — arxiv download: true, max download: 10
```

也可单独使用：

```text
/aris-1-2-arxiv "attention mechanism"
/aris-1-2-arxiv "2301.07041" — download
```

### 飞书 / Lark 集成（可选）

支持两种模式：
- **push**：只发通知
- **interactive**：通知 + 在飞书中交互

最小 push 配置：

```bash
cat > ~/.claude/feishu.json << 'EOF'
{
  "mode": "push",
  "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_ID"
}
EOF
```

interactive 模式和更完整的桥接配置请参考原项目相关说明或本仓库已有文档。

## 全部 Skills

### 0.x 总入口与全流程

| Skill | 功能 | Codex MCP？ |
|-------|------|:---:|
| [`aris-0-1-research-pipeline`](skills/aris-0-1-research-pipeline/SKILL.md) | 端到端：工作流 1 → 1.5 → 2 → 3 | 是 |

### 1.x Idea 阶段

| Skill | 功能 | Codex MCP？ |
|-------|------|:---:|
| [`aris-0-2-idea-discovery`](skills/aris-0-2-idea-discovery/SKILL.md) | 工作流 1 编排 | 是 |
| [`aris-1-1-research-lit`](skills/aris-1-1-research-lit/SKILL.md) | 多源文献搜索 | 否 |
| [`aris-1-4-idea-creator`](skills/aris-1-4-idea-creator/SKILL.md) | idea 生成与筛选 | 是 |
| [`aris-1-5-novelty-check`](skills/aris-1-5-novelty-check/SKILL.md) | 查新验证 | 是 |
| [`aris-1-6-research-review`](skills/aris-1-6-research-review/SKILL.md) | 单轮深度评审 | 是 |
| [`aris-1-7-research-refine`](skills/aris-1-7-research-refine/SKILL.md) | 方法精炼 | 是 |
| [`aris-1-8-experiment-plan`](skills/aris-1-8-experiment-plan/SKILL.md) | 实验规划 | 否 |
| [`aris-1-9-research-refine-pipeline`](skills/aris-1-9-research-refine-pipeline/SKILL.md) | 精炼 + 实验规划流水线 | 是 |

### 2.x 实验阶段

| Skill | 功能 | Codex MCP？ |
|-------|------|:---:|
| [`aris-0-3-experiment-bridge`](skills/aris-0-3-experiment-bridge/SKILL.md) | 实现、sanity check、部署、收结果 | 否 |
| [`aris-2-1-run-experiment`](skills/aris-2-1-run-experiment/SKILL.md) | 运行实验 | 否 |
| [`aris-2-2-monitor-experiment`](skills/aris-2-2-monitor-experiment/SKILL.md) | 监控实验 | 否 |

### 3.x Review 阶段

| Skill | 功能 | Codex MCP？ |
|-------|------|:---:|
| [`aris-3-1-auto-review-loop`](skills/aris-3-1-auto-review-loop/SKILL.md) | 自动 review 循环 | 是 |
| [`aris-3-3-analyze-results`](skills/aris-3-3-analyze-results/SKILL.md) | 分析实验结果 | 否 |
| [`aris-3-4-auto-review-loop-llm`](skills/aris-3-4-auto-review-loop-llm/SKILL.md) | OpenAI 兼容 API 版本 review 循环 | 否 |

### 4.x 写作阶段

| Skill | 功能 | Codex MCP？ |
|-------|------|:---:|
| [`aris-4-7-paper-writing`](skills/aris-4-7-paper-writing/SKILL.md) | 工作流 3 编排 | 是 |
| [`aris-4-1-paper-plan`](skills/aris-4-1-paper-plan/SKILL.md) | 论文大纲与 claims-evidence 矩阵 | 是 |
| [`aris-4-2-paper-figure`](skills/aris-4-2-paper-figure/SKILL.md) | 图表与 LaTeX 表格生成 | 可选 |
| [`aris-4-3-paper-illustration`](skills/aris-4-3-paper-illustration/SKILL.md) | 方法示意图 | 否 |
| [`aris-4-4-paper-write`](skills/aris-4-4-paper-write/SKILL.md) | 逐节 LaTeX 写作 | 是 |
| [`aris-4-5-paper-compile`](skills/aris-4-5-paper-compile/SKILL.md) | 编译 PDF | 否 |
| [`aris-4-6-auto-paper-improvement-loop`](skills/aris-4-6-auto-paper-improvement-loop/SKILL.md) | 自动润色循环 | 是 |

### 5.x 投稿后阶段

| Skill | 功能 | Codex MCP？ |
|-------|------|:---:|
| [`aris-5-1-rebuttal`](skills/aris-5-1-rebuttal/SKILL.md) | rebuttal 流水线 | 是 |
| [`aris-5-2-paper-slides`](skills/aris-5-2-paper-slides/SKILL.md) | 论文报告幻灯片 | 否 |
| [`aris-5-3-paper-poster`](skills/aris-5-3-paper-poster/SKILL.md) | 论文海报 | 否 |

### 工具类

| Skill | 功能 | Codex MCP？ |
|-------|------|:---:|
| [`aris-1-2-arxiv`](skills/aris-1-2-arxiv/SKILL.md) | arXiv 搜索、下载、摘要 | 否 |
| [`aris-9-1-feishu-notify`](skills/aris-9-1-feishu-notify/SKILL.md) | 飞书通知 | 否 |
| [`aris-9-3-pixel-art`](skills/aris-9-3-pixel-art/SKILL.md) | 像素风 SVG 插图 | 否 |

## 替代模型组合

如果你不使用默认的 Claude Code + Codex MCP 组合，也可以保留相同工作流，替换执行者或审稿人模型。

> 推荐默认组合；替代组合更适合已有现成基础设施或 API 配置的场景。

| 方案 | 执行者 | 审稿人 | 需要 Claude API？ | 需要 OpenAI API？ | 配置指南 |
|---|--------|--------|:---:|:---:|---------|
| 默认 | Claude Opus/Sonnet | GPT-5.4（Codex MCP） | 是 | 是 | 本 README 安装流程 |
| A | GLM-5（Z.ai） | GPT-5.4（Codex MCP） | 否 | 是 | 见下方 |
| B | GLM-5（Z.ai） | MiniMax-M2.7 | 否 | 否 | [`docs/MINIMAX_MCP_GUIDE.md`](docs/MINIMAX_MCP_GUIDE.md) |
| C | 任意 CC 兼容 | 任意 OpenAI 兼容 | 否 | 否 | [`docs/LLM_API_MIX_MATCH_GUIDE.md`](docs/LLM_API_MIX_MATCH_GUIDE.md) |
| D | Kimi-K2.5 / Qwen3.5+ | GLM-5 / MiniMax-M2.7 | 否 | 否 | [`docs/ALI_CODING_PLAN_GUIDE.md`](docs/ALI_CODING_PLAN_GUIDE.md) |
| E | DeepSeek-V3.1 / Qwen3-Coder | DeepSeek-R1 / Qwen3-235B | 否 | 否 | [`docs/MODELSCOPE_GUIDE.md`](docs/MODELSCOPE_GUIDE.md) |
| F | Codex CLI (GPT-5.4) | Codex `spawn_agent` (GPT-5.4) | 否 | 是 | [`skills/skills-codex/`](skills/skills-codex/) |
| G | Codex CLI | Claude Code CLI（`claude-review` MCP） | 否* | 否* | [`docs/CODEX_CLAUDE_REVIEW_GUIDE_CN.md`](docs/CODEX_CLAUDE_REVIEW_GUIDE_CN.md) |
| H | Antigravity | GPT-5.4（Codex MCP）或 llm-chat | 否 | 可选 | [`docs/ANTIGRAVITY_ADAPTATION_CN.md`](docs/ANTIGRAVITY_ADAPTATION_CN.md) |
| I | Codex CLI | Gemini direct API（`gemini-review` MCP） | 否 | 否 | [`docs/CODEX_GEMINI_REVIEW_GUIDE_CN.md`](docs/CODEX_GEMINI_REVIEW_GUIDE_CN.md) |

\* 通常依赖本地 CLI 登录态，不强制要求 API key。

### 方案 A：GLM + GPT

只替换执行者（Claude → GLM），保留 GPT-5.4 通过 Codex MCP 审稿。

```bash
npm install -g @anthropic-ai/claude-code
npm install -g @openai/codex
codex setup
```

在 `~/.claude/settings.json` 中配置：

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "your_zai_api_key",
    "ANTHROPIC_BASE_URL": "https://api.z.ai/api/anthropic",
    "API_TIMEOUT_MS": "3000000",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "glm-4.5-air",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "glm-4.7",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "glm-5"
  },
  "mcpServers": {
    "codex": {
      "command": "/opt/homebrew/bin/codex",
      "args": ["mcp-server"]
    }
  }
}
```

### 其他方案

- 方案 B：[`docs/MINIMAX_MCP_GUIDE.md`](docs/MINIMAX_MCP_GUIDE.md)
- 方案 C：[`docs/LLM_API_MIX_MATCH_GUIDE.md`](docs/LLM_API_MIX_MATCH_GUIDE.md)
- 方案 D：[`docs/ALI_CODING_PLAN_GUIDE.md`](docs/ALI_CODING_PLAN_GUIDE.md)
- 方案 E：[`docs/MODELSCOPE_GUIDE.md`](docs/MODELSCOPE_GUIDE.md)
- 方案 G：[`docs/CODEX_CLAUDE_REVIEW_GUIDE_CN.md`](docs/CODEX_CLAUDE_REVIEW_GUIDE_CN.md)
- 方案 H：[`docs/ANTIGRAVITY_ADAPTATION_CN.md`](docs/ANTIGRAVITY_ADAPTATION_CN.md)
- 方案 I：[`docs/CODEX_GEMINI_REVIEW_GUIDE_CN.md`](docs/CODEX_GEMINI_REVIEW_GUIDE_CN.md)

## 说明

- 如需查看项目背景、设计动机、效果展示、路线图、引用方式等信息，请直接访问原项目：
  - [wanshuiyin/Auto-claude-code-research-in-sleep](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep)
- 本 README 保留和“怎么安装、怎么配置、怎么用”直接相关的内容；其中**全流程**与**替代模型组合**属于实际使用路径，因此已保留。

## License

MIT
