---
title: Claude Code 工作原理：上下文、工具、Skills、Hooks 与 Subagents
date: 2026-07-19 14:02:37
tags: [Claude Code, Agent, Context Engineering, MCP]
categories: [AI 工程]
---

Claude Code 看起来像一个能在终端里写代码的聊天机器人，但如果只把它理解成“模型加了一个 Shell”，很多现象就解释不通：为什么同一个任务换个会话结果差很多？为什么工具越接越多，效果反而可能变差？为什么写了 CLAUDE.md 仍然会漏掉硬性步骤？为什么 Subagent 开多了之后，主会话反而不知道项目改到哪里了？

我现在更愿意把 Claude Code 看成一个运行在工程环境里的 Agent Runtime：模型负责判断下一步做什么，客户端负责装配上下文、暴露工具、执行权限控制，并把执行结果送回模型。它真正的能力不只取决于模型，而取决于上下文、动作、控制、隔离和验证能不能形成闭环。

这篇文章不尝试逆向 Claude Code 的私有实现，而是从使用者能观察和配置的系统边界出发，拆解它为什么能工作，以及怎样让它稳定工作。

## 一、先把 Claude Code 拆成六层

![Claude Code 的六层能力模型](/post/code/image.png)

这六层分别解决不同问题：

- `CLAUDE.md / rules / memory`：告诉 Claude 当前项目是什么、有哪些长期约束；
- `Tools / MCP`：赋予它读文件、改代码、运行命令和访问外部系统的动作能力；
- `Skills`：按需加载一套领域知识或标准工作流；
- `Hooks`：在确定的生命周期事件上强制执行脚本、检查或审计；
- `Subagents`：把探索或并行任务放进隔离上下文；
- `Verifiers`：用测试、Lint、构建、日志、截图和 CI 判断结果是否真的成立。

只强化其中一层，系统会失衡。CLAUDE.md 写得太长，上下文先被自己污染；工具堆得太多，模型难以选对；Subagents 到处开，决策和状态容易漂移；验证被跳过，最后只能得到“看起来写完了”的代码。

## 二、核心不是回答，而是 Agentic Loop

![Claude Code 的代理循环](/post/code/image-1.png)

一次完整任务通常会经历这样的循环：

```text
理解目标
  ↓
收集上下文 → 制定下一步 → 调用工具 → 读取结果 → 验证
     ↑                                      ↓
     └────────── 未完成或验证失败，继续 ───────┘
```

模型不会一次性生成整个正确答案。它会先读取目录、搜索符号或查看 Git 状态，基于当前证据决定下一步，然后把工具返回的内容继续加入上下文。只要任务没有完成，或者验证结果不可信，这个循环就会继续。

因此，Agent 的质量可以从五个 surface 来检查：

![Claude Code 的五个系统表面](/post/code/image-2.png)

1. **Context surface**：模型此刻知道什么，哪些内容常驻，哪些按需加载；
2. **Action surface**：它能执行哪些动作，参数和返回值是否清晰；
3. **Control surface**：哪些动作需要批准、限制或阻断；
4. **Isolation surface**：哪些任务应进入独立会话、Subagent 或 Worktree；
5. **Verification surface**：系统凭什么判断任务真的完成。

结果不稳定时，不要第一反应就怪模型。先检查它拿到的上下文是否一致、工具返回是否含噪、权限边界是否模糊，以及有没有可靠的完成条件。

## 三、先分清 CLAUDE.md、MCP、Plugin、Skill、Hook 和 Subagent

![Claude Code 扩展机制的职责边界](/post/code/image-3.png)

这些概念经常一起出现，但它们不是同一层的替代品。

### CLAUDE.md 与 rules：项目契约

CLAUDE.md 适合放每次会话都需要知道的内容：构建命令、目录边界、编码约定、禁止事项和关键架构决策。`.claude/rules/` 可以进一步按路径或文件类型拆分规则，让只和某个子目录有关的说明在需要时再加载。

它们能影响模型行为，但不是强制执行层。像“绝不提交密钥”“修改后必须运行格式化”这种不能依赖模型记忆的规则，应该交给权限系统、Hook 或 CI。

### Built-in Tools 与 MCP：动作能力

内置工具负责文件、搜索、命令等本地动作。MCP 是外部能力接入协议，可以把 GitHub、数据库、监控平台或内部服务暴露成结构化工具与资源。

Tool 回答的是“能做什么”，不负责告诉 Claude 一套完整工作方法。

### Skill：按需加载的方法论

Skill 更像一份可执行 Runbook：什么场景触发、按什么顺序做、什么算完成、失败时在哪里停止。它运行在主会话语境中，适合代码评审、发布、排障和文档生成等可复用工作流。

### Hook：确定性控制层

Hook 在 `PreToolUse`、`PostToolUse`、`Stop`、`PreCompact` 等事件上运行。它可以执行脚本、阻断动作或把检查结果反馈给 Claude。它解决的是“这件事必须发生”，而不是“希望模型记得做”。

### Subagent：隔离上下文的工作单元

Subagent 拥有独立上下文和可限制的工具集合，适合大范围搜索、并行研究、专门审查和产生大量中间输出的任务。它的核心价值不是“多一个模型”，而是隔离噪声和权限。

### Plugin：分发层

Plugin 用来把 Skills、Hooks、Subagents、MCP 配置等能力打包分发。它是容器，不是 Agent Runtime 里的新原语。

一句话记忆：给 Claude 新动作，用 Tool/MCP；给它一套做事方法，用 Skill；必须强制执行，用 Hook；需要隔离上下文，用 Subagent；需要跨项目交付整套能力，用 Plugin。

## 四、上下文工程：最稀缺的不是长度，而是信噪比

很多人把上下文理解成一个容量数字，但实际更重要的是：哪些信息什么时候进入，以及它们会停留多久。

![不同能力进入上下文的时机](/post/code/image-4.png)

会话启动时，系统提示、CLAUDE.md、自动记忆、Skill 描述等内容会占用一部分上下文。随着任务推进，文件内容、命令输出、模型回复和 Hook 返回会持续累积。Skill 正文一般在使用时加载，Subagent 的大规模读取留在它自己的上下文里，只把结果摘要带回主会话。

### 不要再把 MCP 开销写成固定公式

早期或关闭 Tool Search 的配置里，MCP 工具定义可能在启动时整体进入上下文，因此“接入多个 Server 后固定开销很大”确实成立。下面这张图可以看成这种模式下的示意，而不是所有版本都成立的定律。

![MCP 工具全部预加载时的上下文成本示意](/post/code/image-5.png)

当前 Claude Code 默认使用 MCP Tool Search：启动时主要加载工具名和 Server instructions，完整 Schema 在需要时再发现和载入。因此不能简单说“一个 Server 固定消耗多少 token”。真正应该检查的是 `/context` 给出的当前会话分布，以及某个 MCP 是否被配置为始终加载。

![使用 context 命令观察实际上下文分布](/post/code/image-6.png)

### 推荐的上下文分层

```text
始终常驻    → CLAUDE.md：项目契约、构建命令、架构边界
条件加载    → rules：目录、语言、文件类型相关规则
按需加载    → Skills：工作流和领域知识
隔离加载    → Subagents：大规模探索、并行研究、冗长输出
上下文外执行 → Hooks：格式化、审计、阻断和通知
```

这里有几个很实用的判断：

- CLAUDE.md 保持短、具体、可验证；官方建议单个文件尽量控制在 200 行以内；
- 大型参考资料放进 Skill 的 supporting files，需要时再读；
- 命令输出先过滤再返回，不要把几万行日志原样塞进会话；
- 用 `/context` 看真实占用，不要凭感觉猜；
- 任务彻底切换时用 `/clear`，保留同一任务但历史过长时用 `/compact`；
- 重要决策写回仓库文件，不要只存在聊天历史里。

### 压缩不是无损存档

`/compact` 会用摘要替换较长的会话历史。项目根目录的 CLAUDE.md、无路径条件的 rules 和自动记忆会重新注入，但路径规则、子目录 CLAUDE.md 等内容要等相应文件再次读取才会恢复。

所以真正重要的架构决策、修改清单、验证状态和未完成事项，最好写进 `HANDOFF.md`、设计文档或 Issue。会话摘要可以帮助继续工作，但不应该成为项目唯一的事实来源。

![继续、恢复与分叉会话的区别](/post/code/image-7.png)

## 五、Plan Mode：把探索成本和修改副作用分开

![探索阶段与执行阶段](/post/code/image-8.png)

Plan Mode 的工程价值不是“多写一份计划”，而是让 Agent 在没有文件修改副作用的阶段先完成代码搜索、约束确认和方案比较。

对跨模块重构、数据迁移、安全边界调整这类任务，我更喜欢让计划至少回答四件事：

1. 哪些事实已经从代码中确认；
2. 哪些仍是假设，需要谁确认；
3. 准备修改哪些文件或模块；
4. 如何验证，以及失败后如何回滚。

![一个适合复杂改造任务的 Plan Mode Prompt](/post/code/image-9.png)

计划不是越长越好。它的价值是提前暴露错误假设，让执行阶段少走回头路。对于简单的单文件修复，直接做再验证通常更划算；对于高风险改动，先计划再交叉审查，收益很高。

## 六、Skills：不是 Prompt 收藏夹，而是可复用工作流

一个好的 Skill 通常包含四部分：触发条件、执行步骤、停止条件和输出格式。

```yaml
---
name: release-check
description: Use before a release to verify build, version, and smoke tests.
disable-model-invocation: true
---

## Checks
1. Run the production build.
2. Verify the version and changelog.
3. Run smoke tests.
4. Stop on any failure.

## Output
Return Pass/Fail and evidence for every check.
```

`disable-model-invocation: true` 适合有发布、删除、外部消息等副作用，或者必须由用户明确触发的 Skill。常规只读工作流则可以依靠清晰的 description 让 Claude 判断何时使用。

Skill 的核心设计原则是渐进式披露：

```text
.claude/skills/incident-triage/
├── SKILL.md              # 任务语义、边界、步骤和导航
├── runbook.md            # 详细处置手册
├── examples.md           # 示例
└── scripts/
    └── collect-context.sh
```

SKILL.md 不需要把所有知识都吞进去。它应该告诉 Claude 去哪里找细节，并优先调用确定性脚本收集证据。

常见反模式包括：description 模糊到任何任务都能触发、一个 Skill 同时覆盖 review/deploy/debug 五种流程、正文塞进几百页参考资料，以及有副作用却允许自动调用。

## 七、工具设计：目标不是功能最多，而是最不容易选错

给 Agent 的工具和给人使用的 API，设计重点不完全一样。人可以在文档里慢慢辨认十几个相似接口，模型面对的却是有限上下文中的工具名、描述、参数和返回值。

![面向 Agent 的好工具与坏工具](/post/code/image-10.png)

几个实用原则：

- 名称包含资源与动作，例如 `github_pr_get`、`sentry_errors_search`；
- 每个工具只承担一个明确目标，避免万能 `query` 或 `do_action`；
- 参数名体现业务语义，不要全是 `id`、`name`、`target`；
- 大响应支持分页、过滤或 `concise / detailed` 两种格式；
- 返回内容直接服务于下一步决策，隐藏无关内部字段；
- 错误信息说明如何修正参数，而不是只返回 opaque error code；
- 高风险动作明确区分只读、预览和执行。

工具调用前让 Claude 在几个结构化选项中确认范围，往往比给它一个包罗万象的接口更可靠。

![通过结构化选择缩小工具动作范围](/post/code/image-11.png)

Tool Search 解决的是“不要把所有工具 Schema 一次性塞进上下文”，但它不会自动修复糟糕的命名和边界。工具被发现之后，模型仍然需要判断选哪个、参数怎么填、结果是否可信。

## 八、Hooks：把希望模型遵守，升级为系统强制执行

CLAUDE.md 里的“修改后请运行格式化”只是一条行为指令。模型可能忘记，也可能因为上下文冲突而忽略。Hook 则可以在每次编辑后确定性运行格式化或 Lint。

一个简单的思路是：

```text
PreToolUse   → 阻止读取密钥、危险删除、越权命令
PostToolUse  → 格式化、Lint、记录改动证据
Stop         → 检查测试是否执行、任务是否仍有未完成项
PreCompact   → 在压缩前保存必要状态或执行审计
SessionEnd   → 清理临时资源、发送通知
```

但 Hook 也不能滥用。每次工具调用都执行昂贵脚本，会让 Agent 变慢；Hook 输出太长，同样会污染上下文；用 Hook 代替需要推理的设计判断，则会制造大量误拦截。

我的原则是：确定性、低成本、必须执行的事情放 Hook；需要理解上下文和权衡的事情放 Skill 或交给模型。

## 九、Subagents：隔离优先，并行其次

Subagent 最有价值的场景不是“让更多 Agent 一起热闹”，而是下面三类：

- 需要阅读大量文件，但主会话只需要结论；
- 不同子任务可以独立并行，且写入边界不会冲突；
- 希望限制模型、工具或权限，例如只读安全审查。

每个普通 Subagent 会从新的隔离上下文开始，不会自动拥有主会话全部对话和已经读取的文件。主 Agent 必须给出清晰的委托：目标、范围、已知事实、禁止事项、期望输出和完成条件。

一个糟糕的委托是：“看看这里有没有问题。”

更好的委托是：

```text
只读审查 src/auth/ 下的鉴权逻辑。
重点检查权限绕过和 token 生命周期。
不要修改文件。
每个发现必须给出文件、行号、触发路径和严重级别；
如果没有可验证问题，明确返回无发现。
```

并行也有成本。多个 Agent 同时修改同一文件、共享同一工作区或依赖彼此未完成的结果，会把协调成本推回主会话。能独立验收的任务才适合并行；强依赖链仍然应该顺序执行。

## 十、验证闭环：Agent 说“完成”不等于工程完成

Claude Code 最后仍然需要外部证据证明结果成立。验证器可以是：

- 单元测试、集成测试和类型检查；
- Lint、格式化和静态分析；
- 构建产物、运行日志和退出码；
- 浏览器截图、DOM 状态和网络请求；
- Git diff、CI 状态和部署后的真实页面。

一个可靠的完成条件应该能被机器观察：

```text
错误条件：功能写完了，应该可以。

可验证条件：
1. npm test 退出码为 0；
2. npm run build 成功；
3. 登录失败返回 401；
4. 页面不存在 console error；
5. git diff 只包含约定范围内的文件。
```

Agentic Loop 的最后一步不是生成答案，而是拿证据对照完成条件。如果验证失败，就回到上下文收集和行动阶段，而不是用一段解释把失败包装成成功。

## 十一、一套更稳的落地顺序

如果要给一个项目逐步引入 Claude Code，我会按这个顺序：

1. 先写一份短的 CLAUDE.md，只放命令、边界和关键约定；
2. 明确最小验证闭环，让测试和构建先能被自动执行；
3. 把高频、可重复的方法沉淀成 Skills；
4. 把必须执行的格式化、安全阻断和审计放进 Hooks；
5. 只接入任务真正需要的 MCP，并检查工具命名与返回规模；
6. 最后再为高噪声或可并行任务设计 Subagents。

这个顺序背后的逻辑是：先建立事实和完成标准，再扩展动作能力，最后才增加自治与并行度。否则 Agent 做得越快，偏离目标也可能越快。

## 写在最后

Claude Code 的上限取决于模型，但日常工程体验更多取决于系统设计。

上下文决定它看见什么，Tools/MCP 决定它能做什么，Skills 决定它按什么方法做，Hooks 决定哪些规则不能绕过，Subagents 决定噪声和权限如何隔离，Verifiers 决定结果是否值得相信。

真正稳定的 Agent 系统，不是给模型无限上下文、无限工具和无限自治，而是让每一层边界清楚，并让“收集上下文—采取行动—验证结果”这个循环能够持续闭合。

## 参考资料

- [Claude Code：上下文窗口与压缩机制](https://code.claude.com/docs/en/context-window)
- [Claude Code：CLAUDE.md、rules 与 memory](https://code.claude.com/docs/en/memory)
- [Claude Code：Skills](https://code.claude.com/docs/en/slash-commands)
- [Claude Code：Hooks](https://code.claude.com/docs/en/hooks)
- [Claude Code：Subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code：MCP 与 Tool Search](https://code.claude.com/docs/en/mcp)
