# Worklog

> 这里不是日记本，而是 `self-evolution` 的工作卡点账本。
> 核心用途：把真实工作里暴露出来的问题，转成可复用能力资产。

默认路线（写死）：

**真实工作里发现卡点 → 当场解决 → 沉淀成脚本 / skill / 模板 / 工作流 → 下次更稳、更快、更强。**

---

## 使用方法

每次真实工作里遇到以下情况，都应该记一条：
- 搜索不稳
- 抓取不稳
- skill 卡点
- 自动化链路不稳
- 某一步太依赖临场运气
- 某个问题今天解决了，但下次还可能复发

记录时优先参考：
- `bottleneck-template.md`
- `worklog-radar-loop.md`（当需要借外部巡逻补能力缺口时使用）

---

## 工作卡点记录

### 模板
- 日期：
- 工作场景：
- 本次目标：
- 卡点：
- 当场怎么处理：
- 根因判断：
- 沉淀动作：
- 已落盘到：
- 下次更稳的做法：

---

### 2026-04-17：搜索 / 抓取路线不稳，反推 self-evolution 主线（首个完整真闭环样板）
- **工作场景：** 实际工作里需要去两个网站查资料，并尝试走现有网页抓取 / 搜索路线。
- **本次目标：** 尽快拿到可用信息，同时判断当前工具链是否稳定。
- **卡点：** Firecrawl 不稳，内置搜索也不稳，导致“先把眼前任务做完”这件事过于依赖临场切换路线。
- **当场怎么处理：** 先不把问题停留在“今天先这样”，而是把这类问题重新定义成 `self-evolution` 的能力缺口来源。
- **根因判断：** 不是单一网页故障，而是“搜索 / 抓取 / 备用路线 / 可复用执行方式”还不够成体系。
- **外部巡逻触发：** 已按 `worklog-radar-loop.md` 启动一轮与卡点相关的外部巡逻，当前先选 `agent` 作为第一轮贴近主题的 radar topic。
- **对应巡逻输出：**
  - 原始结果：`skills/self-evolution-radar/patrol-run-agent-2026-04-17.txt`
  - 摘要结果：`skills/self-evolution-radar/patrol-summary-agent-2026-04-17.md`
- **本轮外部巡逻回写结论：**
  - Reddit 侧暴露的有效信号，不是单一工具名，而是“更轻量、更本地、更低门槛、更可连续运行”的方向在持续升温；这说明以后补工作流时，要优先考虑**稳定、可替换、可长期跑**，而不是只追单点最强工具。
  - GitHub 候选里，`ComposioHQ/awesome-claude-skills`、`FlowiseAI/Flowise`、`affaan-m/everything-claude-code` 至少提示了一件事：外部世界对 **skills / agent workflow / reusable patterns** 的组织方式，值得继续拆读并借结构。
  - 当前最值得回灌的不是某一个神奇网站，而是：
    1. 把“原始抓取结果”和“结构化判断”拆开输出；
    2. 给不同路线保留备用路径，而不是只押一个抓取源；
    3. 逐步形成固定 summary 模板，减少每次从零判断。
- **沉淀动作：**
  - 已明确 `self-evolution` 的默认路线：真实工作里发现卡点 → 当场解决 → 沉淀成脚本 / skill / 模板 / 工作流。
  - 已将 `self-evolution-radar` 的主题重新校正为“与实际工作结合的自我进化 skill”，而不只是外部巡逻。
  - 已补出 `worklog`、`bottleneck-template`、`worklog-radar-loop` 三个入口，形成第一版闭环骨架。
  - 对这类问题，下一步应继续补：
    - 备用抓取路线清单
    - 本机脚本 fallback
    - 可复用巡逻脚本
    - topic / watchlist 外置配置
- **已落盘到：**
  - `self-evolution/README.md`
  - `self-evolution/worklog.md`
  - `self-evolution/worklog-radar-loop.md`
  - `skills/self-evolution-radar/SKILL.md`
  - `skills/self-evolution-radar/README.md`
  - `skills/self-evolution-radar/patrol-summary-agent-2026-04-17.md`
  - `memory/2026-04-17.md`
  - `self-evolution/fallback-search-and-crawl-workflow.md`
- **下次更稳的做法：**
  - 以后遇到同类卡点，不只解决当前任务，还要同步判断：能不能顺手补成脚本、模板、skill 或备用路径。
  - 如果已经明显需要外部输入找方法和实现，就按 `worklog-radar-loop.md` 启动一轮与卡点相关的 radar 巡逻，再把结论回写到本条记录。
  - 后续要把这类卡点继续往前推进成一个明确资产：**搜索 / 抓取不稳时的备用工作流**。
  - 这条备用工作流文档当前已落到：`self-evolution/fallback-search-and-crawl-workflow.md`，后续遇到同类任务应优先按该顺序执行，而不是临场乱切路线。
- **第四轮真实闭环联动测试（追加验证）：**
  - 已重新按真实闭环顺序执行一次：读取该 worklog 卡点 -> 选 `agent` topic -> 跑 `self-evolution-radar` -> 读取 summary -> 回写结论。
  - 本轮测试输出：
    - `skills/self-evolution-radar/loop-test-agent-raw.txt`
    - `skills/self-evolution-radar/loop-test-agent-summary.md`
  - 本轮再次验证的关键点不是“脚本能跑”，而是 `worklog -> radar -> summary -> 回写` 这条链路在真实卡点上可复现。
  - 新一轮 summary 给出的直接可回灌点依旧稳定：
    1. 原始材料与结构化判断应持续拆开输出；
    2. 应尽快引入轻量评分字段；
    3. 需要把摘要模板长期固定下来，形成可比较历史。
  - 因此，这条首个样板现在已经不只是“做过一次”，而是**至少完成了两轮可复现闭环验证**。

### 2026-04-17：模型路由查询容易被本地文件误导
- **工作场景：** 用户追问当前会话模型与连接地址，且要求给出准确路由。
- **本次目标：** 准确回答当前模型相关的 provider / baseUrl，不用猜。
- **卡点：** 直接看工作区 `models.json` 容易得出与当前 OpenClaw 实际配置不一致的答案，导致“静态文件”和“当前生效配置”混淆。
- **当场怎么处理：** 先承认仅看 `models.json` 不够，再改用 `openclaw config get models` 与 `openclaw config get agents.defaults.model` 交叉核对。
- **根因判断：** 这是典型的 **文档 / SOP 缺失 + 工作流顺序不稳**，不是单一模型配置问题。
- **沉淀动作：** 已补出一份固定排查顺序文档，明确“先看 status / 会话，再看合并配置，再看 agent 默认指向，最后才看本地文件”。
- **已落盘到：**
  - `self-evolution/openclaw-model-route-debug.md`
- **下次更稳的做法：**
  - 以后凡是用户问“你现在是什么模型 / 连接地址是什么”，默认先走这份 SOP；
  - 不再把 `models.json` 当当前唯一真相；
  - 若 `/status`、provider 定义、agent 默认指向互相打架，明确区分“provider 地址”和“当前默认会话路由地址”。

---

## 说明

如果某次问题只靠“经验”解决，但没有沉淀成文件，那不算完成。

`self-evolution` 里真正算数的，不是口头说自己变强了，
而是：
- 文件多了
- 工作流更稳了
- 下次更快了
- 重复错误变少了
