# Auto Research Skills

`auto-research` 是一套同时面向 Claude 和 Codex agent 的分阶段 CS/AI 科研 skill 集合。它覆盖从研究主题收敛到论文草稿产出的完整链路，并通过明确的阶段契约与完整性约束，防止伪造引用、无证据结论和偷偷降级 baseline 这类问题。

## 包含的 Skill

- `auto-research`：全流程总控
- `auto-research-ideation`：文献挖掘与研究点生成
- `auto-research-method`：方法形式化与实验设计
- `auto-research-execution`：实验实现、监控与复现执行
- `auto-research-writing`：论文写作、自审与修订

## 设计原则

- `Evidence first`：所有 claim 和表格都必须能追溯到实验产物或已验证引用。
- `Stage contracts`：每个阶段都通过 `runs/<run_id>/` 下的文件进行读写交接。
- `Output-first writing`：写作从结果、限制和可审查性出发，而不是先堆措辞。
- `Reviewer realism`：整套流程按顶会 reviewer 会怎么挑问题来设计。
- `Budget honesty`：算力预算、baseline 和失败标准都必须在执行前锁定。
- `Human accountability`：生成的论文只是草稿，提交前必须由人审阅和负责。

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

1. 将一个或多个 skill 文件夹复制到你的 Claude 或 Codex skills 目录中。
2. 需要跑完整流程时调用 `auto-research`，只想从某一阶段继续时直接调用对应的 stage skill。
3. 只有在 Stage 3 的实验产物已经存在时，才使用 `auto-research-writing`。

## 兼容性

- 真正可移植的核心是 `SKILL.md`、`references/` 和 `assets/`，Claude 风格和 Codex 风格的 skill 系统都可以使用。
- `agents/openai.yaml` 只是为了 Codex / OpenAI 兼容界面提供元数据，不会妨碍在 Claude 中使用。
- 这套工作流本身不绑定具体模型，核心依赖是：分阶段文件交接、工具可用性，以及必要的人类审批节点。

## 说明

- 这个仓库针对的是 CS/AI 科研工作流，不是通用学术写作工具。
- 写作阶段支持把失败结果诚实地组织成 negative-result framing，而不是“洗论文”。
- `auto-research-writing` 默认提供通用 NeurIPS 风格 LaTeX 模板，同时附带 ICLR 和 ICML 版本。
- 这套东西是科研辅助基础设施，不是自动投稿系统。
