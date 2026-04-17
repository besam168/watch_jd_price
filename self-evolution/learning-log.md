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
