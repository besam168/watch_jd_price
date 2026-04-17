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

### 2026-04-17：第三方 skill 改造后上传 GitHub，容易被总工作区与嵌套 `.git` 带偏
- **工作场景：** 从第三方仓库拉取一个 skill，在工作区内改造成 OpenClaw 版本后，准备再推到新的独立 GitHub 仓库。
- **本次目标：** 只发布目标 skill 本身，不把总工作区杂项、嵌套仓库状态或无关文件一起带上去。
- **卡点：** 第三方 skill 自带 `.git`，先被主工作区误识别成 embedded repo / submodule；同时总工作区本身很脏，直接从根目录观察 `git status` 会被大量无关修改淹没，导致发布边界不清。
- **当场怎么处理：** 先把 skill 收口成纯 OpenClaw 版，再去掉旧 `.git`，并明确“不从总工作区直接推独立仓库”，而是以 skill 目录本身作为发布边界。
- **根因判断：** 这是典型的 **工作流顺序不稳 + 文档 / SOP 缺失**，不是 GitHub 本身有问题。
- **沉淀动作：** 已补出一份专门的发布 SOP，固定“收口 skill -> 检查/移除旧 `.git` -> 不在总工作区直接推 -> 独立 init/commit/push”的顺序。
- **已落盘到：**
  - `self-evolution/skill-publish-workflow.md`
- **下次更稳的做法：**
  - 以后凡是“第三方 skill 改造后再发布”，默认先读这份 SOP；
  - 发布边界永远以 skill 目录为准，不以总工作区为准；
  - 若目录来自 clone，默认先检查是否残留 `.git`，再决定是否独立初始化仓库。 

### 2026-04-17：Claude Code 切第三方兼容路由时，容易把根地址和 `/v1` 配反
- **工作场景：** 用户给出第三方兼容接口地址、key 和模型名，要求“给 Claude Code 配上”，并立即验证是否可用。
- **本次目标：** 让本机 Claude Code 正确切到新模型路由，并用最小真测确认不是假成功。
- **卡点：** 用户通常给的是 OpenAI 风格 `/v1` 地址，但 Claude Code 侧更像要吃根地址；如果照抄 `/v1`，容易出现路径拼错、表面已写入、实际不可用。
- **当场怎么处理：** 直接查看 `.claude/settings.json`，把 `ANTHROPIC_BASE_URL` 改成根地址写法，并统一所有模型字段到目标模型，然后立刻执行 `claude -p` 做最小真测。
- **根因判断：** 这是典型的 **不同工具的兼容接口行为差异 + SOP 缺失**，不是单一 key 或模型名问题。
- **沉淀动作：** 已补出一份 Claude Code 专用的路由配置 workflow，明确“先看配置 -> 默认优先根地址 -> 统一模型族字段 -> 最小真测”的固定顺序。
- **已落盘到：**
  - `self-evolution/claude-code-route-config-workflow.md`
- **下次更稳的做法：**
  - 以后给 Claude Code 切第三方兼容供应方，默认先按这份 workflow 走；
  - 不把 OpenClaw 的 provider 地址写法直接套到 Claude Code；
  - 没跑过 `claude -p` 最小真测前，不对外宣称“已经配好”。

### 2026-04-17：Codex CLI 真测里“回到目标文本”不等于“进程已干净退出”
- **工作场景：** 用 `codex exec` 做最小路由真测，目标是验证 provider / model / key 是否可用。
- **本次目标：** 准确判断 Codex CLI 这次测试到底成功到哪一层，不把请求成功和进程收口混在一起。
- **卡点：** 日志里已经拿到了 `CODEX_ROUTE_OK`，说明模型请求层成功；但 tool 侧进程仍显示 `still running`，后续又收到 `SIGKILL` 系统消息，导致“到底算成功还是失败”口径容易混乱。
- **当场怎么处理：** 把这次结果拆成两层：请求层成功、进程层未完全收口；不再把“拿到目标输出”直接等同于“整个 CLI exec 生命周期完全健康”。
- **根因判断：** 这是典型的 **自动化验收口径不够分层 + CLI 进程生命周期认知不足**，不是单一 provider 或 key 问题。
- **沉淀动作：** 已补出一份 Codex CLI exec completion workflow，明确“先看目标输出，再看是否自然退出”的双层验收顺序。
- **已落盘到：**
  - `self-evolution/codex-cli-exec-completion-workflow.md`
- **下次更稳的做法：**
  - 以后凡是 `codex exec` 验收，都默认区分“请求层成功”和“进程层成功”；
  - 只有两层都过，才说“完整成功”；
  - 若只拿到目标输出但进程未正常收口，对外必须带上边界说明。 

---

### 2026-04-18：`scheduled-report-mailer` 的质量门与发送策略不一致，容易造成系统认知与实际行为偏差
- **工作场景：** 评估 `self-evolution` 是否能从 `self-evolution-radar` 迁移到第二个 skill，并优先选定 `scheduled-report-mailer` 作为生产型 / 流水线型验证对象。
- **本次目标：** 先不急着大改 `scheduled-report-mailer`，而是把当前最关键、最适合纳入 `self-evolution` 的真实 bottleneck 固定成第一条 worklog 样板。
- **卡点：** 文档、配置、日志三者对“partial 时到底发不发”给出的口径不完全一致：README 曾写 `strict_block` / `block`，但当前 `report-config.json` 配置与运行日志显示的是 `send_with_warning` 路线；这会让维护者误判系统实际行为。
- **具体不稳定表现：**
  - README 中存在“`pass` 才发正式邮件，`partial` / `fail` 阻断发送”的描述；
  - 当前配置文件 `delivery_policy.send_on_partial` 实际为 `send_with_warning`；
  - 日志中已多次出现“状态：部分通过”但随后仍然 `SEND_OK` 的记录。
- **影响了什么：**
  - 会让人以为质量门比实际更严格；
  - 容易导致“以为系统会拦，但其实已经发了”的流程误判；
  - 后续若继续接自动化或交接他人维护，风险会被放大。
- **如果不处理，下次还会不会重复踩坑：** 会，而且这不是一次性表述问题，而是会反复影响验收口径、发送决策与对外汇报边界。
- **当场怎么处理：** 本轮先不仓促修改发送策略本身，而是先把这条问题固定收口成 `self-evolution` worklog，明确它属于“工作流顺序不稳 + 文档/SOP 缺失 + 配置/运行口径分离”的生产型 bottleneck。
- **当前结果：**
  - [ ] 已彻底解决
  - [ ] 仅临时绕过
  - [x] 部分解决
  - [ ] 还没解决
- **根因判断：**
  - [ ] 搜索不稳
  - [ ] 抓取不稳
  - [ ] skill 设计缺口
  - [ ] 脚本能力不足
  - [x] 工作流顺序不稳
  - [ ] 外部服务不稳定
  - [x] 文档 / SOP 缺失
  - [x] 其他：配置口径、文档口径、运行事实没有被统一到一个可验证来源
- **我当前对根因的判断：**
  - 不是单一配置错了这么简单，而是“生产链路中的真实行为”还没有被定义成唯一准绳；
  - 文档更新、配置调整、日志观察三者之间缺少一个固定收口流程；
  - 因此这类问题很适合作为 `self-evolution` 迁移到第二个 skill 的第一条样板。
- **应沉淀成什么：**
  - [ ] 一个小补丁
  - [ ] 一个新脚本
  - [ ] 一个备用路径
  - [ ] 一个新 skill
  - [ ] 一个模板
  - [x] 一个更稳的执行顺序
  - [x] 一段文档 / SOP
  - [x] 其他：一条“质量门策略验收基线”记录
- **具体应该沉淀为：**
  - 一条固定检查顺序：先看当前配置，再看最近运行日志，再决定 README/OPS 文档是否需要对齐；
  - 一条明确验收口径：`partial` 是否允许发送，必须以当前配置 + 最近有效运行日志为准，不能只信旧文档；
  - 后续可进一步扩展成 `scheduled-report-mailer` 的“质量门策略对齐 SOP”。
- **下次更稳的做法：**
  - 下次遇到同类问题，先看 `config/report-config.json` 的真实值，再看 `logs/*.log` 中最近一次 `SUMMARY` / `SEND` 行为；
  - README 和运维文档应视作待对齐资产，而不是运行真相本身；
  - 若要改发送策略，必须同时更新配置、README、OPS_CHECKLIST，并做一次最小真测留痕；
  - 以后“质量门策略”应被视为可审计的工作流接口，而不只是说明文字。
- **已落盘到：**
  - `self-evolution/worklog.md`
  - `memory/2026-04-18.md`
- **已更新脚本 / skill / 模板：**
  - 暂未改 `scheduled-report-mailer` 代码；当前先完成 bottleneck 固定收口与方法层接入。
- **是否已 git 提交：** 本轮待提交。
- **下一个跟进动作：**
  1. 视需要补一份 `scheduled-report-mailer` 的质量门策略对齐 SOP；
  2. 再决定是否引入一轮与“质量门 / 发送策略 / 生产型 skill 可靠性”相关的外部 radar 输入；
  3. 若继续推进第二个 skill 验证，可围绕这条记录补第一轮“配置 -> 日志 -> 文档对齐”最小闭环。

---

## 说明

如果某次问题只靠“经验”解决，但没有沉淀成文件，那不算完成。

`self-evolution` 里真正算数的，不是口头说自己变强了，
而是：
- 文件多了
- 工作流更稳了
- 下次更快了
- 重复错误变少了
