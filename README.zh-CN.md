# Auto Research Skills

`auto-research` 是一套同时面向 Claude 和 Codex agent 的分阶段 CS/AI 科研 skill 集合。它会先询问你想投哪个会议或期刊，再从官方来源抓取对应的 LaTeX 模板和投稿要求，结合 CFP 分析创新角度，然后再推进从研究主题收敛到论文草稿产出的完整链路，并通过明确的阶段契约与完整性约束，防止伪造引用、无证据结论和偷偷降级 baseline 这类问题。

## 包含的 Skill

- `auto-research`：全流程总控
- `auto-research-ideation`：文献挖掘与研究点生成
- `auto-research-method`：方法形式化与实验设计
- `auto-research-execution`：实验实现、监控与复现执行
- `auto-research-writing`：论文写作、自审与修订

## 设计原则

- `Evidence first`：所有 claim 和表格都必须能追溯到实验产物或已验证引用。
- `Stage contracts`：每个阶段都通过 `runs/<run_id>/` 下的文件进行读写交接。
- `Venue-first setup`：在 ideation 之前先确定目标会议或期刊，再用 CFP 和官方模板约束创新点与论文包装。
- `Output-first writing`：写作从结果、限制和可审查性出发，而不是先堆措辞。
- `Reviewer realism`：整套流程按顶会 reviewer 会怎么挑问题来设计。
- `Budget honesty`：算力预算、baseline 和失败标准都必须在执行前锁定。
- `Human accountability`：生成的论文只是草稿，提交前必须由人审阅和负责。
- `No evaluation-paper drift`：除非用户明确要求，否则流程不会默认退化成纯 benchmark / 纯评测论文。
- `External figure handoff`：当流程图或 idea 图更适合外部模型生成时，写作阶段会保留 LaTeX 占位符，并把可直接给 Gemini、GPT-image 等外部图像模型的提示词保存下来。
- `Venue-aware writing budget`：写作阶段会严格服从目标会议页数限制，并在空间允许时默认给 `Related Work` 预留约 1 到 1.5 页、尽量做到引用丰富。

## 仓库结构

```text
auto-research/
auto-research-ideation/
auto-research-method/
auto-research-execution/
auto-research-writing/
README.md
README.en.md
README.zh-CN.md
```

每个 skill 目录包含：

- `SKILL.md`：触发条件和工作流说明
- `references/`：按需加载的参考材料
- `assets/`：模板、脚本或 LaTeX 资源
- `agents/openai.yaml`：面向 Codex / OpenAI 兼容界面的元数据；在 Claude 侧可以忽略

## 快速开始

1. 将一个或多个 skill 文件夹复制到你的 Claude 或 Codex skills 目录中（具体路径见下方 [安装](#安装)）。
2. 需要跑完整流程时调用 `auto-research`，只想从某一阶段继续时直接调用对应的 stage skill。
3. 只有在 Stage 3 的实验产物已经存在时，才使用 `auto-research-writing`。

## 安装

### Claude Code

Claude Code 会自动从 `~/.claude/skills/`（用户级，全局可用）或 `<project>/.claude/skills/`（项目级，仅当前仓库可用）发现 skill。把这五个目录复制或软链过去即可：

```bash
# 用户级：在所有项目中可用
mkdir -p ~/.claude/skills
cp -r auto-research auto-research-ideation auto-research-method \
      auto-research-execution auto-research-writing ~/.claude/skills/

# 或项目级：仅在当前仓库内可用
mkdir -p .claude/skills
cp -r auto-research auto-research-ideation auto-research-method \
      auto-research-execution auto-research-writing .claude/skills/
```

复制完成后重启 Claude Code（或运行 `/skills` 确认列表里已出现这五个 skill）。各 `SKILL.md` 中声明的触发短语（例如「write me a paper on X」「auto research X」「做一篇关于 X 的论文」）会自动触发对应 skill，你也可以按名字直接调用某个阶段。

### Codex / OpenAI 兼容 agent

把同样的目录放入你的 Codex 风格 runtime 所使用的 skills 目录即可，`agents/openai.yaml` 提供对应的 UI 元数据。

## 兼容性

- 真正可移植的核心是 `SKILL.md`、`references/` 和 `assets/`，Claude 风格和 Codex 风格的 skill 系统都可以使用。
- `SKILL.md` 的 frontmatter（`name` + `description`）就是 Claude Code 期望的格式，无需任何转换，所有 description 也都在 Claude Code 1024 字符上限内。
- `agents/openai.yaml` 只是为了 Codex / OpenAI 兼容界面提供元数据，Claude Code 会直接忽略，不会报错。
- 这套工作流本身不绑定具体模型，核心依赖是：分阶段文件交接、工具可用性，以及必要的人类审批节点。

## 说明

- 这个仓库针对的是 CS/AI 科研工作流，不是通用学术写作工具。
- 写作阶段支持把失败结果诚实地组织成 negative-result framing，而不是“洗论文”。
- `auto-research-writing` 默认提供通用 NeurIPS 风格 LaTeX 模板，同时附带 ICLR 和 ICML 版本。
- 这套东西是科研辅助基础设施，不是自动投稿系统。
- 默认目标是真正的研究创新 idea，而不是“测很多模型、跑很多榜单”的评测论文。
- 对于流程图、方法图、idea 图，写作阶段支持保留占位符并输出给 Gemini、GPT-image 之类外部作图模型使用的提示词文件。
