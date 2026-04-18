# Learning Log

## 当前双引擎阵地
- GitHub（学实现、学结构、学工作流）
- Reddit（看热点、看趋势、看用户反馈）

## 当前阶段目标
- 增强 Skill 设计能力
- 增强 Agent / Workflow 编排能力
- 增强自动化落地能力
- 增强文档与边界表达能力
- 增强模板化与产品化能力

---

## 候选池

### 待补充
- （后续每次轻巡逻时追加）

---

## Reddit 热点记录模板
- 日期：
- 板块：
- 热门话题：
- 反复出现的关键词：
- 用户真实痛点：
- 是否值得去 GitHub 深挖：
- 备注：

---

## 深读记录

### 2026-04-17 第一次真实巡逻
- **Reddit 最值得追的话题：** 本地模型与轻量化部署/本地运行能力持续升温，尤其是：
  - `Qwen3.6-35B-A3B released!`
  - `24/7 Headless AI Server on Xiaomi 12 Pro (Snapdragon 8 Gen 1 + Ollama/Gemma4)`
  - `1-bit Bonsai 1.7B (290MB in size) running locally in your browser on WebGPU`
- **观察结论：** 这说明“更轻、更本地、更低门槛部署”仍然是持续热点，不只是模型参数竞赛。
- **GitHub 候选 repo：**
  1. `https://github.com/NousResearch/hermes-agent`
  2. `https://github.com/browser-use/browser-use`
  3. `https://github.com/firecrawl/firecrawl`
  4. `https://github.com/google-gemini/gemini-cli`
- **当前最值得深读：** `NousResearch/hermes-agent`
- **原因：**
  - 直接命中当前正在调查的 `Hermes`
  - 同时属于 agent / tool calling / workflow 交叉点
  - 对后续“我总控，执行层 agent 干活”的路线有直接价值
- **本轮可回灌升级点：**
  - 以后做“自我进化巡逻”时，优先从社区热议里找“真实需求信号”，再去 GitHub 对应 repo 找“真实实现信号”，不要只盯技术名词本身。

### 模板
- 日期：
- Repo：
- 方向：
- 解决的问题：
- 最值得抄的 3 个点：
- 文档/结构亮点：
- 风险/边界：
- 可迁移方法：
- 回灌动作：

---

## Heartbeat 推进记录

### 2026-04-18 中午前 heartbeat：OpenClaw Claude `/v1/messages` 已从施工单推进到第一轮真实代码落刀
- **本次 heartbeat 做了什么：** 把 OpenClaw 兼容 Claude `/v1/messages` 这条线，从“最终施工单”正式推进到第一轮真实代码改造：已直接修改本机 dist 与 gateway 类型定义，补入最小 `anthropic-messages` 入口骨架。
- **为什么做这件事：** 这条兼容改造此前已经把路由、auth wrapper、runtime bridge、response mapper 都写成了接近实装版方案，如果 heartbeat 还停留在继续写文档，就会变成“方案很完整，但永远不动刀”。当前最有价值的小事，不是再写新草案，而是把第一刀真的切进去，验证方案是否能落到运行时结构上。
- **解决了什么问题 / 捕捉到什么信号：**
  - 已在 `gateway-cli-CWpalJNJ.js` 中补入第一轮最小模块：`getAnthropicApiKey(...)`、`authorizeAnthropicMessagesRequest(...)`、`handleAnthropicPostJsonEndpoint(...)`、`normalizeClaudeCompatModel(...)`、`extractTextFromClaudeContent(...)`、`buildClaudeMessagesPrompt(...)`、`buildClaudeAgentCommandInput(...)`、`runAnthropicMessageViaAgentRuntime(...)`、`createClaudeMessageResponse(...)`、`handleAnthropicMessagesHttpRequest(...)`；
  - 已在 `createGatewayHttpServer(...)` 中接入 `anthropic-messages` stage，使 `/v1/messages` 不再只停留在文档层；
  - 已在 `types.gateway.d.ts` 中补入 `GatewayHttpMessagesConfig` 与 `GatewayHttpEndpointsConfig.messages`；
  - 当前这条线的阶段性状态已从“方案级完成”推进到“最小实现骨架已进 runtime 文件”，下一步最值钱的是跑最小验收，而不是继续扩 streaming / tools / multimodal。
- **沉淀到哪里：**
  - `self-evolution/learning-log.md`
  - 当天 `memory/2026-04-18.md`
- **下次接着做什么：**
  - 先验 `POST /v1/messages` 不再 404；
  - 再验 `x-api-key` 能否过 auth；
  - 再验 text-only 最小请求能否打回 `CLAUDE_MESSAGES_OK`。

### 2026-04-18 上午 heartbeat：补记 `scheduled-report-mailer` collect 日志已切 run-id 单文件
- **本次 heartbeat 做了什么：** 把 `scheduled-report-mailer` collect-only 排障线里一个已经跑实的关键修补正式记账：`collect_comprehensive_report.py` 现已支持按 `run-id` 输出单独日志文件，同时保留总日志；并且已做最小验证，确认 root 总日志里多段 `COLLECT START/END` 不是单 run 内部重入，而是多次运行混写同一文件造成的视觉误判。
- **为什么做这件事：** 之前总日志混写会严重污染判断：明明是在看某一轮 collect，却很容易被历史 run 的 `START/END` 干扰，导致误以为单个 collect 脚本内部重复触发。把日志按 run-id 拆开，本质上是在补“排障观测面不干净”这个真实能力缺口。
- **解决了什么问题 / 捕捉到什么信号：**
  - `collect_comprehensive_report.py` 现会输出 `RUN_ID` 与 `RUN_LOG`，并把当前轮日志写入 `logs/collect_comprehensive_report-<RUN_ID>.log`；
  - `latest_collect_status.json` 现新增 `runId` 与 `runLogPath`；
  - 结合这套 run-id 观测后，已验证单轮 run 在 root 总日志中只有 1 次 `COLLECT START`，并未出现“同一 run 自己刷多段 `START/END`”；
  - 说明之前看到的多段 `COLLECT START/END`，本质上是不同运行共写 `logs/collect_comprehensive_report.log`，而不是单脚本内部重入。
- **沉淀到哪里：**
  - `collect_comprehensive_report.py`
  - `self-evolution/learning-log.md`
  - 当天 `memory/2026-04-18.md`
- **下次接着做什么：**
  - 直接基于单轮 `run-id` 独立日志继续查“为什么单次 collect 本身久不结束”；
  - 若后续仍需多人/多轮并发排障，可继续补“单实例锁 / 入口幂等保护 / run-id 分状态目录”的下一层 SOP。

### 2026-04-18 上午 heartbeat：把 Claude `/v1/messages` 的 `x-api-key` 认证入口正式收口成 wrapper 草案
- **本次 heartbeat 做了什么：** 把 OpenClaw 适配 Claude `/v1/messages` 这条线里最后一个还没钉死的实现卡点——`x-api-key` 认证入口——正式沉淀成文档，新增 `ANTHROPIC_MESSAGES_AUTH_WRAPPER_DRAFT.md`。
- **为什么做这件事：** 当前 `/v1/messages` 的 request parser、runtime bridge、response mapper 草案已经基本成形，但如果认证入口还停留在口头提醒，第一轮实现依然容易卡死在“Claude 客户端请求进不来”这一步。这属于典型的工程闭环只差最后一层胶水。
- **解决了什么问题 / 捕捉到什么信号：**
  - 已明确当前不适合让 Claude 入口硬套 `handleGatewayPostJsonEndpoint(...)`，因为它先做通用 auth，而 Claude 更可能走 `x-api-key`；
  - 已明确第一轮最稳路线是新增两个最小函数：`authorizeAnthropicMessagesRequest(...)` 与 `handleAnthropicPostJsonEndpoint(...)`；
  - 已把“`x-api-key` 临时映射成 Bearer，再复用现有 gateway auth/scope/body 读取逻辑”的接近实装版伪代码写实；
  - 说明当前这条 OpenClaw 兼容改造线，已经从“路由 / handler / runtime bridge”进一步收口到“认证入口胶水层”级别。
- **沉淀到哪里：**
  - `ANTHROPIC_MESSAGES_AUTH_WRAPPER_DRAFT.md`
  - 当天 `memory/2026-04-18.md`
- **下次接着做什么：**
  - 可以把 `/v1/messages` 第一轮实现所需模块清单汇总成最终执行单；
  - 或直接进入真实代码改造阶段。

### 2026-04-18 上午 heartbeat：补记 `scheduled-report-mailer` collect-only 的阶段心跳与重复触发嫌疑
- **本次 heartbeat 做了什么：** 把 `scheduled-report-mailer` 这条真实排障链最新推进正式记账：一方面已给 `run-job.py` 加上阶段心跳与中途 state 落盘，另一方面已确认 `evaluate-report.py` 的 `contentCoverageGate` 需要兼容 `📊 实时头条` 新结构；继续往下排时，又新暴露出 `collect` 阶段可能存在“重复触发 / 多轮重入”现象。
- **为什么做这件事：** 这条链如果只记“外层又 SIGKILL 了”，信息密度太低，下次仍然得从头扒开。当前最值钱的不是记结果，而是把排障口径分层：外层 exec 生命周期、`run-job.py` 阶段可见性、评估解析正确性、以及 `collect` 真正耗时 / 重入来源，要分别记录。
- **解决了什么问题 / 捕捉到什么信号：**
  - 已给 `run-job.py` 增加 `plan:start / plan:done / collect:start / ...` 这类阶段心跳，并把 `lastStage` / `lastStageAt` 写入 `last-<job>.json`，因此外层再被杀时，至少能知道停在哪一段；
  - 已修掉 `evaluate-report.py` 只认旧版 `一、重要头条新闻` 的问题，使其兼容当前报告里的 `📊 实时头条（过去24-48小时）`，避免把明明有头条的报告误判成 `contentCoverageGate.ok = false`；
  - 已进一步确认当前 collect 主耗时面不只是 whitelist probe，而在 `daily_comprehensive_report.py` 的 `discover_news_via_multi_search()` 与 `enrich_news_items_with_evidence()`；
  - 已先做一轮降载：减少搜索引擎数、topic 数、discovery 总量与 evidence 抓取数；
  - 但最新 root 侧日志又显示连续多段 `===== COLLECT START ===== ... ===== COLLECT END rc=0 =====`，说明下一步最该排查的是：到底是单次 collect 太重，还是同一链路被重复启动 / 多轮任务叠加写同一日志。
- **沉淀到哪里：**
  - `self-evolution/learning-log.md`
  - 当天 `memory/2026-04-18.md`
- **下次接着做什么：**
  - 区分 root 日志里的多段 `COLLECT START/END` 究竟来自单进程内部重入，还是多个独立 collect 进程共用同一日志；
  - 若确认存在并发 / 重复触发，再补一条 `scheduled-report-mailer` 的“单实例锁 / 幂等保护 / 日志分 run-id” SOP。

### 2026-04-18 上午 heartbeat：把 OpenClaw Claude/Codex 兼容改造的源码锚点写死进施工清单
- **本次 heartbeat 做了什么：** 给 `OPENCLAW_CLAUDE_CODEX_BUILD_CHECKLIST.md` 增补了一节“已确认的源码锚点”，把本机 dist 里已经定位到的关键函数和大致位置直接写死。
- **为什么做这件事：** 这类源码入口如果只留在聊天上下文里，下次很容易又花时间重翻一次。把锚点写进施工清单，本质上是在补“后续实现切入速度”这个很小但真实的能力缺口。
- **解决了什么问题 / 捕捉到什么信号：**
  - 已把 `createGatewayHttpServer`、`requestStages`、`handleOpenAiModelsHttpRequest`、`handleOpenAiHttpRequest`、`handleOpenResponsesHttpRequest`、`GatewayHttpEndpointsConfig`、`GatewayHttpConfig` 的源码锚点写死；
  - 已明确 `anthropic-messages` stage 最自然的插入区间，就是 `models/embeddings` 之后、`openresponses/openai` 前后；
  - 说明当前这条 OpenClaw 兼容改造线已经开始从“文档规划”继续收口到“实施锚点固化”层。
- **沉淀到哪里：**
  - `OPENCLAW_CLAUDE_CODEX_BUILD_CHECKLIST.md`
  - 当天 `memory/2026-04-18.md`
- **下次接着做什么：**
  - 继续把 `/v1/messages` 的最小 handler 伪代码骨架补出来；
  - 或直接进入第一轮代码级实现草案。

### 2026-04-18 早晨 heartbeat：补记 `scheduled-report-mailer` collect-only 验证的收口边界
- **本次 heartbeat 做了什么：** 把刚刚围绕 `scheduled-report-mailer` 脚本改造时暴露出的一个真实小坑，正式记到 heartbeat 推进记录里：`evaluate-report.py` 的新分层评估结构已验证，但 `run-job.py --collect-only` 这轮真实运行没有自然收口，最终在外层表现为 exec 会话 `SIGKILL`。
- **为什么做这件事：** 如果不把这层边界记下来，下次很容易把“评估输出结构已经正确”误说成“整条 collect-only 自动化链路已经完全健康”。这属于典型的自动化验收口径不够分层。
- **解决了什么问题 / 捕捉到什么信号：**
  - 已确认 `evaluate-report.py` 新增的 `contentCoverageGate` / `headlineEvidenceGate` 分层输出本身已经生效；
  - 已确认当前还不能直接宣称 `collect-only` 全链路已稳定，因为真实运行会话没有自然收口；
  - 说明 `scheduled-report-mailer` 下一步除了继续调评估逻辑，也应补一条“collect-only 长链路收口 / 超时 / 挂起排查”的小 SOP 或 worklog。
- **沉淀到哪里：**
  - `self-evolution/learning-log.md`
  - 当天 `memory/2026-04-18.md`
- **下次接着做什么：**
  - 追查 `run-job.py --collect-only` 挂住时究竟卡在采集、fallback、子进程等待，还是外层 exec 会话管理；
  - 把“评估脚本结构验收”和“整条 collect-only 自然收口验收”明确拆成两层口径。

### 2026-04-18 早晨 heartbeat：沉淀 OpenClaw 适配 Claude Code / Codex CLI 的真实边界
- **本次 heartbeat 做了什么：** 把刚刚围绕 OpenClaw 兼容 Claude Code / Codex CLI 的本机勘探结果，正式沉淀成两份实施文档：
  - `IMPLEMENTATION_PLAN_OPENCLAW_CLAUDE_CODE_CODEX.md`
  - `GAP_ANALYSIS_OPENCLAW_CLAUDE_CODE_CODEX.md`
- **为什么做这件事：** 这次真实工程任务暴露出一个很容易反复误判的边界：不能把“已有 OpenAI-compatible HTTP surface”直接等同于“已经兼容 Claude Code 和 Codex CLI”。如果不尽快写成文档，后续很容易继续拿泛兼容口径误报工程进度。
- **解决了什么问题 / 捕捉到什么信号：**
  - 已确认本机 OpenClaw 现有公开兼容面包括：`GET /v1/models`、`GET /v1/models/{id}`、`POST /v1/chat/completions`、`POST /v1/responses`；
  - 已确认 `Codex CLI` 方向不是从零开始，而是应先验现有 `/v1/models` + `/v1/responses` 的真实 gap，再做增强；
  - 已确认 `Claude Code` 方向当前不能假设已有现成兼容面，因为尚未在本机勘探中看到公开的 `POST /v1/messages` / Anthropic Messages adapter；
  - 已定位到关键代码入口：`handleOpenAiModelsHttpRequest`、`handleOpenResponsesHttpRequest`、`resolveAgentIdFromModel`、`loadAgentModelIds`、`toOpenAiModel`，说明下一步已经从“空谈方向”推进到“可落具体改造点”。
- **沉淀到哪里：**
  - `IMPLEMENTATION_PLAN_OPENCLAW_CLAUDE_CODE_CODEX.md`
  - `GAP_ANALYSIS_OPENCLAW_CLAUDE_CODE_CODEX.md`
  - 当天 `memory/2026-04-18.md`
- **下次接着做什么：**
  - 继续把网关 HTTP 总路由分发块抓全；
  - 输出 `/v1/messages` 最小 handler 设计草案；
  - 再进入第一轮代码级改造，而不是继续停留在协议口头分析。

### 2026-04-18 早晨 heartbeat：补记 `self-evolution-radar` 的 `--source` 参数边界
- **本次 heartbeat 做了什么：** 把今天轻巡逻里踩到的 `--source all` 无效问题，正式补进 `skills/self-evolution-radar/README.md`。
- **为什么做这件事：** 这类小坑不补文档，下次很容易重复踩，属于典型的“能力缺口虽小，但会反复制造摩擦”。
- **解决了什么问题 / 捕捉到什么信号：**
  - 已明确写清 `--source` 当前合法值是 `both / reddit / github / custom`；
  - 已明确补充“如果想表达两个源都跑，应使用 `--source both`，不是 `all`”；
  - 说明当前 `self-evolution-radar` 已开始从“能跑”继续补到“少踩参数坑”的产品化细节层。
- **沉淀到哪里：**
  - `skills/self-evolution-radar/README.md`
  - 当天 `memory/2026-04-18.md`
- **下次接着做什么：**
  - 若后续再出现同类误写，可继续补到脚本 help 文案或参数别名兼容；
  - 若无新坑，则从候选 repo 里挑一个做 README 级深读。

### 2026-04-18 早晨 heartbeat：补做一轮 agent 轻巡逻并记录脚本参数边界
- **本次 heartbeat 做了什么：** 用 `self-evolution-radar` 围绕 `agent` 主题补跑了一轮最小真实轻巡逻，成功生成：
  - `skills/self-evolution-radar/patrol-run-agent-2026-04-18.txt`
  - `skills/self-evolution-radar/patrol-summary-agent-2026-04-18.md`
- **为什么做这件事：** 当前没有更急的新卡点要补洞，按 `HEARTBEAT.md` 应优先做一次轻巡逻，继续给后续深读与方法回灌积累新信号。
- **解决了什么问题 / 捕捉到什么信号：**
  - 先踩到一个小而真实的参数边界：`--source all` 无效，脚本当前合法值仍是 `both/reddit/github/custom`；
  - 改成 `--source both` 后执行成功，说明这类参数口径值得后续写进脚本帮助文案或 README，避免重复踩坑；
  - 本轮摘要再次暴露出几个持续有效方向：
    - Reddit 侧“更轻、更本地、更低门槛部署”仍然热；
    - GitHub 候选里 `ToolJet/ToolJet`、`ComposioHQ/awesome-claude-skills`、`FlowiseAI/Flowise` 适合作为下一批 README 级深读入口；
    - 当前巡逻输出继续证明“热点发现”和“候选实现筛选”应分段表达，而 repo 轻量评分字段值得继续补。
- **沉淀到哪里：**
  - `skills/self-evolution-radar/patrol-run-agent-2026-04-18.txt`
  - `skills/self-evolution-radar/patrol-summary-agent-2026-04-18.md`
  - 当天 `memory/2026-04-18.md`
- **下次接着做什么：**
  - 可从 `ToolJet / awesome-claude-skills / Flowise` 中挑 1 个做 README 级拆读；
  - 或补一条很小的产品化改进：把 `--source all` 这类错误别名收进帮助文案、README 或 preset 配置里，减少参数面摩擦。

### 2026-04-17 晚间 heartbeat：完成 self-evolution-radar 第三轮功能测试
- **本次 heartbeat 做了什么：** 对 `skills/self-evolution-radar/scripts/run_real_patrol.py` 做了第三轮接口测试，重点验证 `--no-summary` 模式是否正常工作。
- **为什么做这件事：** 前两轮已经验证了最小真测、topic 切换、source 切换和自定义输出路径；这轮补上 `--no-summary`，可以把 V1 原型脚本的主要参数面收口。
- **解决了什么问题 / 捕捉到什么信号：**
  - 已确认命令：
    `python .\\skills\\self-evolution-radar\\scripts\\run_real_patrol.py --topic memory --source github --github-limit 4 --output .\\skills\\self-evolution-radar\\test-memory-raw.txt --no-summary`
    可正常执行；
  - 已确认 raw 文件真实生成：`skills/self-evolution-radar/test-memory-raw.txt`；
  - 已确认 summary 文件不会生成，`--no-summary` 行为符合预期；
  - 说明当前 `self-evolution-radar` 已具备：最小运行、topic/source 切换、自定义输出、可选关闭摘要 这几项核心脚本能力。
- **沉淀到哪里：**
  - `skills/self-evolution-radar/test-memory-raw.txt`
  - 当天 `memory/2026-04-17.md`
- **下次接着做什么：**
  - 可以从“参数面测试”切到“真实闭环联动测试”，也就是从真实 worklog 卡点出发，跑 radar，再回写总结。

### 2026-04-17 晚间 heartbeat：完成 self-evolution-radar 第四轮真实闭环联动测试
- **本次 heartbeat 做了什么：** 从 `worklog` 中“搜索 / 抓取路线不稳”这条真实卡点出发，按 `worklog -> radar -> summary -> 回写` 的顺序，完整跑了一轮真实闭环联动测试。
- **为什么做这件事：** 前三轮主要验证的是脚本接口与参数面；这一轮开始验证 `self-evolution-radar` 是否真的能接进 `self-evolution` 的真实工作流，而不只是独立脚本。
- **解决了什么问题 / 捕捉到什么信号：**
  - 已确认从真实卡点出发重跑 `agent` topic 巡逻是可行的；
  - 已生成：
    - `skills/self-evolution-radar/loop-test-agent-raw.txt`
    - `skills/self-evolution-radar/loop-test-agent-summary.md`
  - 已完成回写到 `self-evolution/worklog.md`；
  - 本轮再次稳定暴露的回灌点包括：原始材料与结构化判断拆开输出、尽快引入轻量评分字段、把摘要模板长期固定下来；
  - 说明 `self-evolution-radar` 现在已不仅是“能跑”，而是**能接进真实闭环**。
- **沉淀到哪里：**
  - `self-evolution/worklog.md`
  - `skills/self-evolution-radar/loop-test-agent-raw.txt`
  - `skills/self-evolution-radar/loop-test-agent-summary.md`
  - 当天 `memory/2026-04-17.md`
- **下次接着做什么：**
  - 不要继续只测同一条闭环；下一步更值钱的是选第二个 skill / 第二类问题，开始做第一轮多 skill / 多场景复用验证。

### 2026-04-17 晚间 heartbeat：补出第三方 skill 改造后独立发布 GitHub 的固定 SOP
- **本次 heartbeat 做了什么：** 针对“第三方 skill 拉到工作区后再改造、再发布到独立 GitHub 仓库”这条真实工作链路，补了一份固定发布 SOP。
- **为什么做这件事：** 这两天真实工作已经暴露出两个稳定坑：一是第三方目录自带 `.git`，容易被主工作区误识别成 embedded repo / submodule；二是总工作区很脏，直接从根目录做发布会让边界失控。
- **解决了什么问题 / 捕捉到什么信号：**
  - 已把“发布边界永远以 skill 目录为准，不以总工作区为准”写成明确原则；
  - 已把“先收口 skill -> 检查/移除旧 `.git` -> 不在总工作区直接推 -> 独立 init/commit/push”固定成顺序；
  - 说明当前 `self-evolution` 不只是补搜索/抓取 fallback，也开始补 **skill 产品化 / 发布链路** 的稳定性。
- **沉淀到哪里：**
  - `self-evolution/skill-publish-workflow.md`
  - `self-evolution/worklog.md`
  - 当天 `memory/2026-04-17.md`
- **下次接着做什么：**
  - 下次真正发布独立 skill 到 GitHub 时，直接按这份 SOP 执行一轮真验收；
  - 若再踩坑，就继续把它补成更细的“仓库初始化 + SSH remote + 首次 push 验收”版本。

### 2026-04-17 深夜 heartbeat：补出 Claude Code 切第三方兼容路由的固定 workflow
- **本次 heartbeat 做了什么：** 把刚刚真实跑通的 Claude Code 换路由过程，沉淀成一份专用 workflow 文档。
- **为什么做这件事：** 这次配置里有一个很容易反复踩坑的点：用户给的是 `/v1` 风格地址，但 Claude Code 更稳的写法通常是根地址；如果不写成 SOP，下次很容易又把根地址和 `/v1` 配反。
- **解决了什么问题 / 捕捉到什么信号：**
  - 已把“默认优先根地址，不盲写 `/v1`”固定下来；
  - 已把“统一模型族字段 + 立刻跑 `claude -p` 最小真测”固定下来；
  - 说明当前 `self-evolution` 已开始覆盖 **本机 coding agent 路由配置** 这类真实工程操作，而不只是外围调研与 skill 文档。
- **沉淀到哪里：**
  - `self-evolution/claude-code-route-config-workflow.md`
  - `self-evolution/worklog.md`
  - 当天 `memory/2026-04-17.md`
- **下次接着做什么：**
  - 下次再切 Claude Code 供应方时，直接按这份 workflow 执行；
  - 若再遇到特殊兼容差异，就继续补“Claude Code / OpenClaw / Codex 三者路由差异对照表”。

### 2026-04-17 深夜 heartbeat：补出 Codex CLI exec 完成判定的双层验收 SOP
- **本次 heartbeat 做了什么：** 把刚刚 `codex exec` 真测里暴露出的“请求层成功但进程层未完全收口”问题，沉淀成一份专用验收 SOP。
- **为什么做这件事：** 这次最小真测里已经拿到了 `CODEX_ROUTE_OK`，说明模型请求层成功；但 tool 进程随后没有及时自然退出，并最终出现 `SIGKILL` 系统消息。如果不把这层区别写清楚，下次很容易把“拿到目标文本”误判成“整条 CLI 生命周期完全成功”。
- **解决了什么问题 / 捕捉到什么信号：**
  - 已把 Codex CLI 验收拆成“请求层成功”和“进程层成功”两层；
  - 已把“先看目标输出，再看是否自然退出”固定成顺序；
  - 说明当前 `self-evolution` 已开始覆盖 **coding agent 自动化验收口径**，不再只停留在配置和路由本身。
- **沉淀到哪里：**
  - `self-evolution/codex-cli-exec-completion-workflow.md`
  - `self-evolution/worklog.md`
  - 当天 `memory/2026-04-17.md`
- **下次接着做什么：**
  - 下次再做 Codex CLI 真测时，默认先按这份双层口径判断结果；
  - 若同类现象重复出现，再继续补“Codex CLI 短任务退出行为”专项排查记录。

### 模板
- 日期：
- 本次 heartbeat 做了什么：
- 为什么做这件事：
- 解决了什么问题 / 捕捉到什么信号：
- 沉淀到哪里：
- 下次接着做什么：

---

## 周报记录

### 模板
- 周期：
- 本周 Reddit 热点：
- 本周 GitHub 深读：
- 本周学到的方法：
- 可落地改进：
- 不值得追的坑：
- 下周主看方向：
