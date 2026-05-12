<div align="center">

# 📝 auto-research

### 扔个主题,出篇论文。<br/>证据为先 · Reviewer 视角 · 你最后过目。

*对 Claude Code 或 Codex 说一句:* **`帮我做一篇关于 X 的 NeurIPS 论文`**
*→ 5 阶段流水线 → reviewer 风格自审 → 你署名负责。*

<!-- 想加手绘 hero 图,把生成结果丢到 docs/hero.png 即可,
     docs/hero-prompt.md 里有可直接喂给 GPT-image-1 / Midjourney / Gemini 的 prompt。
     图缺失也不影响 README,下面的 mermaid 流程图就是默认 hero。 -->

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?logo=python&logoColor=white)](#)
[![LaTeX](https://img.shields.io/badge/LaTeX-TeXLive-008080.svg?logo=latex&logoColor=white)](#)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Compatible-D97757.svg)](https://claude.ai/code)
[![Codex](https://img.shields.io/badge/Codex-Compatible-10A37F.svg?logo=openai&logoColor=white)](#)
[![Skills](https://img.shields.io/badge/Skills-5-8A2BE2.svg)](auto-research/SKILL.md)
[![Venues](https://img.shields.io/badge/Venue%20targets-NeurIPS%20%C2%B7%20ICLR%20%C2%B7%20ICML%20%C2%B7%20CVPR%20%C2%B7%20ACL-FF6B35.svg)](#)

</div>

```mermaid
flowchart LR
    U(["👤 你"]) -->|"<b>帮我做一篇关于 X 的论文</b><br/>+ 目标会议、预算、ddl"| O{{"🎯 总控<br/>契约 + 完整性闸"}}
    O --> S0["📋 Stage 0<br/>会议设置<br/><i>抓 CFP +<br/>官方 LaTeX 模板</i>"]
    S0 --> S1["💡 Stage 1<br/>Ideation<br/><i>3 个打分候选<br/>STORM 风格</i>"]
    S1 --> S2["📐 Stage 2<br/>Method<br/><i>公式 + 伪代码<br/>+ 实验计划</i>"]
    S2 --> S3["🧪 Stage 3<br/>Execution<br/><i>训练 + 记录<br/>results.csv + report</i>"]
    S3 --> S4["📄 Stage 4<br/>Writing<br/><i>paper.tex + paper.pdf<br/>+ reviewer 自审</i>"]
    S4 -->|"hand_off.md"| H(["👤 你署名 + 投稿"])
    classDef hot fill:#FFEDD5,stroke:#EA580C,color:#7C2D12,stroke-width:2px;
    classDef cold fill:#DBEAFE,stroke:#2563EB,color:#1E3A8A,stroke-width:2px;
    class O,S0,S1,S2,S3,S4 hot
    class U,H cold
```

<div align="center"><sub><i>每个阶段通过 <code>runs/&lt;run_id&gt;/stageN_*/hand_off.md</code> 交接。可以只跑某一阶段,也可以从中间任意阶段重启。</i></sub></div>

---

`auto-research` 是一套面向 Claude Code 和 Codex agent 的「从研究主题 → 论文草稿」的分阶段 CS/AI 科研 skill 集合。

整体思路是把一篇 AI 顶会论文的写作过程拆成 5 个阶段,每个阶段由一个独立的 skill 负责,阶段之间通过 `runs/<run_id>/` 目录下的文件交接,从而避免「中途崩了得从头来」「论文里出现伪造引用」「baseline 被偷偷换弱」这一类常见翻车。

---

## 一句话理解

> 你告诉它「想投 NeurIPS 一篇关于 X 的论文」，它会先把目标会议的模板和投稿要求抓下来，再依次完成：选 idea → 形式化方法 → 跑实验 → 写 LaTeX 草稿，并在关键节点要你过目。

它**不是**自动投稿系统，也**不是**自动「水论文」工具，最终 PDF 仍需要你自己审稿、署名、负责。

---

## 小白须知（第一次用之前请先看这里）

如果你完全没用过 agent 类工具，建议先按下面顺序完成基础准备，否则直接调用会到处报错。

### 这个 skill 适合谁

- 已经知道自己想做的「研究方向」或「研究问题」，想要一个能帮你跑 baseline、整理结果、写 LaTeX 初稿的协作者。
- 投稿目标是 NeurIPS / ICLR / ICML / CVPR / ACL / EMNLP 等 CS/AI 顶会，或同等级别的期刊。
- 愿意全程「人在环里」（human-in-the-loop）：在 idea、方法、跑实验、改稿这些节点都自己拍板。

### 这个 skill **不适合**谁

- 完全没有研究方向，期望它「自己想出能毕业的课题」——它会给候选 idea，但研究品味仍需要你。
- 想做的是纯文献综述、纯 benchmark 评测、纯工程报告——本流程默认走的是「真正的研究创新」路线。
- 期望它能帮你绕过查重、伪造数据、自动投稿——这些事情本流程**故意**做不到。

### 如果你是刚进课题组的学生（最重要的一步，先做完这个再谈别的）

软件准备再齐全，没有「研究品味」也跑不出有意义的论文。建议**先**完成下面这条线，再去碰这套 skill：

1. **和导师对一次方向**。明确：你这一年（或这学期）的研究方向、要解决的问题、导师能接受的最低产出（顶会一作？workshop？技术报告？）。不要看着 skill 名字就自己脑补一个方向。
2. **请导师或师兄师姐推荐 2–3 篇该方向上近 1–2 年的 SOTA 论文**（NeurIPS / ICLR / ICML / CVPR / ACL 这一档），从头到尾认真读。读的时候重点**不是记住每个数字**，而是看：
   - 它们的 **abstract / introduction / method / experiments / related work** 各自承担什么职能、怎么排版；
   - 它们的 **baseline** 选了哪些、为什么是这些；
   - 它们的 **ablation** 在证明什么；
   - 它们「卖点」是什么、为什么会被这个会议接收，reviewer 当时可能挑了什么刺。
3. 读完之后，**试着用三五句话回答**：「这个方向最强的 3 个方法分别在解决什么子问题？它们各自的弱点是什么？我能不能找到一个它们都没覆盖好的角度？」答得上来，再开始用这套 skill；答不上来，继续读论文。

这一步比下面任何一条软件 / 环境准备都重要。否则 ideation 阶段产出的 idea 你既判断不了好坏，也没法和导师对线，最后只能盲选一个跑掉，浪费算力还得罪导师。

### 第一次使用前需要完成的基础准备

1. **装好 Claude Code 或 Codex CLI**，并能在终端里正常聊一句话。如果连 `claude` / `codex` 命令都没跑通，先不要碰这个 skill。
2. **配好 API key 和账单**：跑完整流程的 token 消耗不算少，建议先确认账户里有可用额度。
3. **准备一个干净的工作目录**（例如 `~/research/`），后续 `runs/<run_id>/` 会全部建在里面。不要在 Desktop 这种到处是文件的目录里跑。
4. **本地能编译 LaTeX**：装好 TeX Live 或 MacTeX，至少能跑通 `pdflatex hello.tex` 再说。Stage 4 需要它来生成 PDF。
5. **准备 Python 环境和（如果有）GPU**：Stage 3 真的会跑训练/评测代码。没有 GPU 也能跑，但要在一开始就把 compute budget 设得很小，否则它会一直挂着烧 token。
6. **大致了解几个名词**：
   - **CFP**（Call for Papers）：会议的征稿启事，规定页数、格式、评审重点。本流程会自动抓。
   - **baseline**：你方法要对比的已有方法。少了它，论文一定被拒。
   - **ablation**：消融实验，证明「你提出的每个组件都不是凑数的」。
   - **run\_id**：一次完整跑流的标识，本流程用它来组织所有中间产物。

   不熟悉也没关系，每个阶段的 `references/` 里都会再展开讲，但起码看到这些词不会一脸懵。
7. **先读一遍 [设计原则](#设计原则)**，特别是 `Evidence first` 和 `Human accountability` 两条，这两条决定了你不能指望它「自己编一个看起来很厉害的结果」。

### 推荐的第一次使用姿势

- **不要一上来就跑全流程**。建议第一次只跑 `auto-research-ideation`，看看它产出的 3 个候选 idea 和打分，感受一下交互节奏。
- 觉得 ok 之后，再用一个**小目标**跑端到端（例如：一个小数据集 + 一个能在一两小时内跑完的方法），先把整套 file hand-off 跑顺。
- 真正投会议的工作再考虑放大 compute budget。

---

## 五个 Skill 各自负责什么

| Skill | 角色 | 输入 | 主要产物 |
|---|---|---|---|
| `auto-research` | 总控（不做研究，只调度） | 你给的方向 + 目标会议 + 预算 + ddl | 建好 `runs/<run_id>/`，依次调用下面四个 skill，把住每次阶段交接 |
| `auto-research-ideation` | 文献挖掘 + idea 生成 | 研究方向 + 目标会议的 CFP | 3 个带打分和真实引用的候选 idea，挑出 1 个 |
| `auto-research-method` | 方法形式化 + 实验设计 | 选中的 idea | `method.md`（含公式和伪代码）+ `experiment_plan.yaml`（数据集、baseline、metric、ablation、种子） |
| `auto-research-execution` | 实际跑实验 | 实验计划 | 训练/评测代码、`results.csv`、`results_summary.json`、`run_report.md` |
| `auto-research-writing` | 写 LaTeX 论文 | 上面所有产物 | `paper.tex` / `paper.pdf` / `references.bib` / `figures/`、reviewer 风格自审 `review.md` |

`auto-research` 自己**不写代码、不查文献、不写论文**。它只负责按顺序调度这 4 个专项 skill，并在每次交接时做完整性检查（没有伪造引用、没有偷偷把 baseline 调弱、没有「没源数据的表格」）。

---

## 中间产物长这样

```
runs/<run_id>/
├── run.yaml                        # 方向、会议、预算、ddl、模式
├── stage0_setup/                   # 目标会议的 LaTeX 模板 + CFP
├── stage1_ideation/
│   ├── candidates.json             # 3 个候选 idea + 打分
│   └── chosen.json                 # 选中的那一个
├── stage2_method/
│   ├── method.md                   # 公式 + 伪代码
│   └── experiment_plan.yaml        # 数据集 / baseline / metric / ablation / seeds
├── stage3_execution/
│   ├── code/                       # 真正的实验仓库
│   ├── logs/
│   ├── results.csv
│   └── run_report.md
└── stage4_writing/
    ├── paper.tex
    ├── paper.pdf
    ├── references.bib
    ├── figures/
    └── review.md                   # reviewer 风格自审
```

---

## 设计原则

- **Evidence first**：论文里的每一个数、每一张表都必须能追到 `runs/<run_id>/results/` 里的源行，写作阶段会拒绝渲染没有源数据的表格单元。
- **Stage contracts**：每个阶段只通过文件交接，禁止「在脑子里记着上一步的结论」。
- **Venue-first setup**：ideation 之前先确定目标会议，把 CFP 和官方模板作为创新角度的约束。
- **Output-first writing**：从结果、limitation、可审查性出发，再考虑措辞。
- **Reviewer realism**：按顶会 reviewer 会怎么挑刺来组织实验和写作。
- **Budget honesty**：算力预算、baseline、失败标准在执行前就锁定。
- **Human accountability**：生成的论文是草稿，提交前必须由你审阅并署名负责。
- **No evaluation-paper drift**：默认不会退化成纯 benchmark / 纯评测论文，除非你明确说要写那种。
- **External figure handoff**：流程图、idea 概念图这类更适合外部模型画的图，写作阶段会留 LaTeX 占位符 + 一份可以丢给 Gemini / GPT-image 的提示词。
- **Venue-aware writing budget**：严格服从会议页数限制，空间允许时默认给 Related Work 留约 1 – 1.5 页，并尽量做到引用丰富。

---

## 安装

### Claude Code

Claude Code 自动从这两个地方发现 skill：

- `~/.claude/skills/`（用户级，所有项目都能用）
- `<project>/.claude/skills/`（项目级，仅当前仓库）

把这 5 个目录复制（或软链）过去即可：

```bash
# 用户级
mkdir -p ~/.claude/skills
cp -r auto-research auto-research-ideation auto-research-method \
      auto-research-execution auto-research-writing ~/.claude/skills/

# 或项目级
mkdir -p .claude/skills
cp -r auto-research auto-research-ideation auto-research-method \
      auto-research-execution auto-research-writing .claude/skills/
```

复制完后重启 Claude Code（或运行 `/skills` 确认这 5 个名字都在列表里）。之后任意一句触发短语都能拉起对应 skill：

- 「做一篇关于 X 的论文」
- 「write me a paper on X」
- 「auto research X」
- 「想投 NeurIPS / ICLR / ICML / CVPR / ACL 的 X」

你也可以按名字直接跳到某个阶段，例如「跑 auto-research-writing，input 在 `runs/2026-05-12-xxx/`」。

### Codex / OpenAI 兼容 agent

把同样这 5 个目录放进你的 Codex skills 目录即可，`agents/openai.yaml` 提供 UI 元数据。

---

## 快速开始（端到端示例）

```text
你：想投 NeurIPS 2026，方向是 small language model 的 test-time compute，
    GPU 是 4×A100，ddl 还有 3 个月。先跑全流程，每阶段交接前都要我确认。

agent：
  → Stage 0：抓 NeurIPS 2026 CFP + LaTeX 模板，写入 runs/2026-05-12-ttc-slm/stage0_setup/
  → Stage 1：mining 文献，给出 3 个候选 idea 和打分 → 等你选
  → Stage 2：把选中的 idea 写成 method.md + experiment_plan.yaml → 等你确认
  → Stage 3：按 plan 跑实验，输出 results.csv + run_report.md
  → Stage 4：写 paper.tex，编译 paper.pdf，附 reviewer 风格自审 review.md
```

只想从某一阶段继续：直接调用对应的 stage skill，并把上一步的 `hand_off.md` 指给它。

---

## 仓库结构

```text
auto-research/
auto-research-ideation/
auto-research-method/
auto-research-execution/
auto-research-writing/
docs/                # hero 图 + 重新生成 hero 图的 prompt
README.md  README.zh-CN.md
```

每个 skill 目录内：

- `SKILL.md`：触发条件 + 工作流
- `references/`：按需加载的参考材料（CFP 解析、state contract、完整性规则等）
- `assets/`：模板、脚本、LaTeX 资源
- `agents/openai.yaml`：Codex 端的 UI 元数据，Claude 侧会忽略，不报错

---

## 兼容性

- 真正可移植的核心是 `SKILL.md` + `references/` + `assets/`，Claude 风格和 Codex 风格的 skill 系统都能跑。
- `SKILL.md` frontmatter 用的是 Claude Code 原生格式（`name` + `description`），所有 description 都在 1024 字符以内。
- `agents/openai.yaml` 只是 Codex / OpenAI 兼容 UI 用的元数据，Claude Code 会直接忽略。
- 整个工作流不绑定具体模型，核心假设只有 3 条：阶段化的文件交接、必要工具的可用性、人工审批节点。

---

## 注意事项

- 这是 CS/AI 科研工作流，不是通用学术写作工具，社科 / 人文 / 临床方向不建议直接套。
- 失败结果支持以 negative-result 的方式诚实地组织成论文，**不会**自动「洗」成正向结论。
- `auto-research-writing` 默认提供 NeurIPS 风格 LaTeX 模板，并附带 ICLR 和 ICML 变体。
- 默认目标是真正的研究创新 idea，而不是「测很多模型、跑很多榜单」的评测论文。
- 流程图、方法图、idea 概念图等更适合外部模型作图的位置，写作阶段会留 LaTeX 占位符并保存对应提示词文件。
- 这套东西是科研辅助基础设施，**不是自动投稿系统**，最终提交永远由人决定。
