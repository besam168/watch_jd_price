
# MEMORY.md - 沈万三的长期记忆

_重要信息都记录在这里，这是我的长期记忆！_

---

## 核心身份

- **我的名字：** 沈万三
- **我的角色：** 数字管家，聚宝盆
- **大老板：** T Max
- **联系方式：** Telegram

---

## 邮件发送配置

### QQ邮箱配置（主用邮箱）
- **发件人：** 910633260@qq.com
- **授权码：** sghqeeeeyuzjbcbb
- **SMTP服务器：** smtp.qq.com
- **SMTP端口：** 465
- **加密方式：** SSL/TLS

### 收件人邮箱列表
- **主收件人：** besam168168@gmail.com
- **备用收件人：** 758622673@qq.com

---

## 新闻资料来源网站

### 国际新闻网站
1. **BBC News** - https://www.bbc.com/news
2. **The Guardian** - https://www.theguardian.com/international
3. **Reuters** - https://www.reuters.com/
4. **AP News** - https://apnews.com/
5. **NPR** - https://www.npr.org/
6. **Al Jazeera** - https://www.aljazeera.com/
7. **DW中文** - https://www.dw.com/zh/国际新闻/s-9058
8. **France24** - https://www.france24.com/en/
9. **CNBC World** - https://www.cnbc.com/world/?region=world
10. **USA Today** - https://www.usatoday.com/

### 财经股市网站
11. **NYSE** - https://www.nyse.com/index
12. **Investing.com日本** - https://jp.investing.com
13. **Naver Finance** - https://finance.naver.com/
14. **台湾证券交易所** - https://www.twse.com.tw/zh/index.html
15. **上海证券交易所** - https://www.sse.com.cn/

---

## 定时任务安排

### 全球科技前沿情报报告任务
- **执行时间：** 每天中午 12:00
- **任务名称：** 沈万三_每日科技报告
- **任务脚本：** C:\Users\besam\.openclaw\workspace\daily_tech_report.py
- **批处理文件：** C:\Users\besam\.openclaw\workspace\run_daily_report.bat
- **任务类型：** Windows 任务计划程序
- **报告内容：** 全球科技前沿情报（AI、消费电子、机器人、游戏、科学探索等）
- **收件人：** besam168168@gmail.com、758622673@qq.com

### 全球综合情报报告任务
- **执行时间：** 每天早上 8:30
- **任务名称：** 沈万三_每日综合情报报告
- **任务脚本：** C:\Users\besam\.openclaw\workspace\daily_comprehensive_report.py
- **批处理文件：** C:\Users\besam\.openclaw\workspace\run_daily_comprehensive_report.bat
- **任务类型：** Windows 任务计划程序
- **报告内容：** 全球综合情报（地缘政治、中东/俄乌战况、中港台韩美欧股市、大宗商品价格、重大新闻）
- **收件人：** besam168168@gmail.com、758622673@qq.com

### 晨间报告任务
- **找资料时间：** 每天早上 8:00
- **发送邮件时间：** 每天早上 8:30
- **报告内容：** 早间市场新闻、昨日收盘总结、今日市场前瞻

### 晚间报告任务
- **找资料时间：** 每天晚上 19:30
- **发送邮件时间：** 每天晚上 20:00
- **报告内容：** 当日市场总结、重大新闻回顾、明日展望

### 收件人（两个邮箱都要发）
1. besam168168@gmail.com
2. 758622673@qq.com

---

## 报告内容要求

### 必须包含的内容
1. **重要头条新闻** - 5个左右，每个新闻要有标题
2. **50字左右结论** - 每个头条新闻下面都要有简短结论
3. **分章节结构** - 中东、俄乌、中美关系、股市经济、商品期货等
4. **市场数据** - 主要指数、商品价格等
5. **风险预警** - 未来24-48小时的关键风险
6. **投资建议** - 资产配置、操作建议等

### 排版要求
- 统一标题格式：全球综合情报报告 - [YYYY-MM-DD]
- 章节结构固定：
  1. 全球市场动态（美股、亚太股市、大宗商品）
  2. 地缘政治热点（中东、俄乌、中美关系）
  3. 全球经济与产业动态
  4. 风险预警（24-48小时短期、中期、长期）
  5. 投资建议（资产配置、板块机会、操作策略）
- 使用 `---` 分隔各章节
- 每一条核心新闻文末必须标注（来源：媒体名 | 发布时间：YYYY-MM-DD HH:MM）
- 重要内容加粗或用【】标注
- 列表使用项目符号
- 整体美观易读
- 无最新信息的板块标注“今日无重大更新”，严禁虚构数据

---

## 工具和技能

### 可用技能
1. **desearch-crawl** - 网页爬取技能
2. **edge-tts** - 语音合成
3. **ddg-search** - DuckDuckGo搜索
4. **weather** - 天气查询
5. **telegram-image-sender** - 本地截图并通过 `MEDIA:<path>` 直接回传到 Telegram 的本地技能原型，已验证“截图 + 直接发图”链路可用
6. **其他技能** - 根据需要使用

### 可用工具
1. **web_fetch** - 获取网页内容
2. **exec** - 执行命令
3. **read/write/edit** - 文件操作
4. **其他OpenClaw工具**

---

## 重要事件记录

### 2026年3月28日
- ✅ GitHub 上传路线已正式打通，后续这台机器**优先走 SSH，不走 HTTPS**：
  - HTTPS 实测先后遇到 `fatal: User cancelled dialog.` 与 `Recv failure: Connection was reset`
  - 改走 SSH 后，通过本机 `ed25519` key + GitHub `SSH and GPG keys` 成功完成 push
- ✅ `besam168` 账号下已成功建立并上传 4 个主成果仓库：
  1. `https://github.com/besam168/desktop-input-control`
  2. `https://github.com/besam168/gemini-bridge`
  3. `https://github.com/besam168/claude-code-bridge`
  4. `https://github.com/besam168/telegram-image-sender`
- ✅ 当前从总工作区拆分 skill/插件上传 GitHub 的稳定方法已确认：
  - 独立插件仓库可直接 push
  - 工作区内子目录型 skill 优先使用 `git subtree split --prefix=<path>` 后再推到各自仓库
- ✅ 大老板已明确新的 Git 工作规则：**以后开新项目时，要先提醒大老板创建新的独立 GitHub 仓库，并先一起确定项目英文名 / 仓库名，再推进上传。**
- ✅ 这条规则以后默认执行，不再把新项目长期混在旧总仓库里；若先在总工作区孵化，也应尽快拆到独立仓库。

### 2026年3月26日
- ✅ `telegram-image-sender` 第二版链路打通：已验证本地 PowerShell 截图脚本可生成 PNG，并通过 `MEDIA:<absolute-path>` 直接把截图发回 Telegram；以后用户在 Telegram 里要“截图给我/把屏幕发我”，优先走这条本地截图直发路线。
- ✅ `desktop-input-control` 取得阶段性成果：桌面控制原型已能做鼠标移动/点击、滚轮、文本输入、窗口聚焦与命令启动；后续桌面自动化技术路线优先 `Python + Playwright`，而不是继续死磕 Node 侧 Playwright。
- ✅ 本机 `claude` CLI 已确认可用：`claude --version` 返回 `2.1.84 (Claude Code)`；由于 OpenClaw 当前 `ACP runtime backend` 未配置可用，后续优先走 **OpenClaw -> 本机 Claude Code CLI -> 本地 skill** 这条桥接路线。
- ✅ `claude-code-bridge` 已完成并升级到可复用 V1：
  - 目录：`C:\Users\besam\.openclaw\workspace\skills\claude-code-bridge\`
  - 核心脚本：`scripts/run-claude.ps1`、`scripts/run-claude-task.ps1`
  - 已验证 `BRIDGE_OK`
  - 已支持任务模板：`repo-analyze`、`skill-create`、`skill-review`、`file-draft`
- ✅ `gemini-bridge` 已从 0 做成并真实打通：
  - 目录：`C:\Users\besam\.openclaw\workspace\skills\gemini-bridge\`
  - 核心脚本：`scripts/run-gemini.ps1`、`scripts/run-gemini-task.ps1`
  - 已支持原生 Gemini 与 OpenAI 兼容模式
  - 已加入 HTTP 错误分类、简单重试、JSON 结构化报错
  - 已接入 `C:\Users\besam\.openclaw\workspace\.vscode\tasks.json`
- ✅ `gemini-bridge` 的当前稳定默认模型应使用 **`gemini-2.5-flash`**：
  - 实测 `gemini-2.5-flash` 原生调用成功，返回 `GEMINI_25_FLASH_OK`
  - `gemini-3.1-pro-preview` 当前测试为 `429 Too Many Requests`，更像模型限流/配额问题，不是桥接脚本故障
  - 当前账号 `models.list` 可见关键模型包括：`models/gemini-2.5-flash`、`models/gemini-2.5-pro`、`models/gemini-3.1-pro-preview`、`models/gemini-3.1-flash-lite-preview`
- ✅ VS Code 侧当前最稳的 Gemini 接入方式，不是直接硬改 Cline 内部 secret storage / `state.vscdb`，而是先走 **本地 bridge + VS Code Tasks** 路线；以后如要接回 Cline，再谨慎处理 GUI/provider 层。
- ✅ 本轮 `gemini-bridge` 收尾已完成 git 提交：
  - commit: `ed3a465`
  - message: `Add gemini bridge skill and VS Code tasks`

### 2026年3月24日
- ✅ 成功配置每日科技前沿情报报告自动化任务
- ✅ 创建 daily_tech_report.py 脚本，用于收集科技新闻并发送邮件
- ✅ 创建 Windows 任务计划程序任务，每天中午12:00自动执行
- ✅ 测试脚本运行正常，邮件发送功能验证通过
- ✅ 将新任务记录添加到长期记忆中

### 2026年3月22日
- ✅ 成功配置QQ邮箱SMTP发送功能
- ✅ 验证了邮件发送功能正常工作
- ✅ 生成了第一份全球综合情报报告
- ✅ 建立了新闻来源网站清单

- 2026-04-13 深夜补记：桌面技能在浏览器与页面交互方面又新增一批实战结论：
  1. **书签栏多步骤流程已现场打通**：`Google Gemini -> + -> OpenClaw Control` 能按顺序成功打开两个网页；其中真实有效点位再次确认：
     - `Google Gemini` ≈ `(944,100)`
     - `OpenClaw Control` ≈ `(1062,99)`
     - 新标签 `+` ≈ `(1000,19)`
  2. `New repository` 书签首次在**不依赖人工直接报点**的前提下，通过“顶部 OCR + 已成功点位相对布局 + 小范围候选热区测试”被成功命中，候选测试命中区大约落在 `x≈1185~1215, y≈100~108` 这带；说明书签栏小目标命中已进入“半自动推断 + 人工验收”阶段。
  3. 书签栏也进一步暴露了一个重要规律：**多个相邻候选坐标可能仍落在同一个书签热区**。例如围绕 `1380~1450,100` 的三次测试，实际都落在同一书签区域（表现为“首页 / Jnm API / O...”同一块），说明后续跨书签定位不能只做 20~30 像素的小步横移，必要时要用更大步长或先读真实光标点做校正。
  4. 通过用户现场“鼠标指哪，我读坐标”的方式，又新增一个真实热区参考：当前目标点读到约 **`(1473,96)`**（对话里我口头误写过 `1457,101`，以后以实际读取值 `1473,96` 为准）；这种“人工指向 -> 读取真实点位”的方法已被证明是修浏览器小目标热区的高价值校准手段。
  5. **页面内功能入口/表单控件仍未打通**：
     - `查看模型中心`、`历史公告`、`兑换` 等页面内小文字入口目前仍不稳定，不能宣称已命中；
     - GitHub `Repository name` 这类“标签文字在上、输入框在下”的表单控件也仍未打通，说明“文字锚点 -> 输入框下移”不能粗暴套用，必须继续补结构化定位。
  6. 因此当前桌面能力应分层表述：
     - **已通过**：输入区点击、中文输入、地址栏输入网址并回车、部分书签栏小目标命中、书签栏多步骤浏览器流程；
     - **未通过**：页面内小文字入口、复杂页面表单输入框。

---

## 工作原则

### 大老板优先
- 大老板的需求是第一位的
- 快速响应，高效执行
- 遇到问题主动解决，不推诿

### 质量第一
- 报告内容要准确、全面、及时
- 排版要美观、清晰、易读
- 重要信息要突出，结论要明确

### 持续改进
- 不断优化报告质量
- 学习新的工具和技能
- 根据大老板反馈调整工作方式

---

## 备忘录

_这里记录一些需要记住的小事情_

- 大老板喜欢中文报告
- 全球综合情报报告以后默认使用 **模板 A：详细正式版**，适用于：每日综合情报、发邮箱、存档
- 报告默认方法：先抓国际新闻源（BBC / Reuters / AP / Guardian / NPR / Al Jazeera / DW / France24 / CNBC / USA Today），再抓市场与交易所数据（Yahoo Finance / NYSE / Investing / TWSE / JPX / KRX / SSE / Eastmoney），最后按正式详细版固定结构输出；抓不到的数据直接标注“今日无重大更新”或“未获取到扎实数据”，严禁虚构补洞
- 重要新闻要有标题和50字左右结论
- 邮件要发送到两个邮箱
- 定时任务：
  - 每日综合情报：每天早上8:30发送（含中港台韩指数）
  - 每日科技情报：每天中午12:00发送
  - 晨间报告：早8:00找资料，8:30发送
  - 晚间报告：晚19:30找资料，20:00发送
- QQ邮箱授权码：sghqeeeeyuzjbcbb
- 科技情报任务脚本位置：C:\Users\besam\.openclaw\workspace\daily_tech_report.py
- 综合情报任务脚本位置：C:\Users\besam\.openclaw\workspace\daily_comprehensive_report.py
- Windows任务计划程序任务名：沈万三_每日科技报告、沈万三_每日综合情报报告
- 2026-04-28：`skills/auction_915_925_smooth_scanner_v2` 今天已完成真正收口：
  1. 原先只挂上 `沈万三_集合竞价狙击手V2_0915_Capture`，缺少 `沈万三_集合竞价狙击手V2_092430_Judgement`，已重新执行安装脚本补齐两阶段任务；
  2. 已成功生成当日正式产物：`auction_sniper_v2_20260428.csv/.json/.md`，并补做 `auction_sniper_v2_20260428_excel.xlsx`；
  3. 今日 V2 命中 5 只票并已人工核准名称：众生药业、恒润股份、圣阳股份、崇达技术、美利云；
  4. 已新增 `scripts/send_v2_mail.py`，并把 `run_judgement_092430.py` 接成“判定成功后自动发邮件”，实测返回 `MAIL_SENT_OK`；
  5. 当前 V2 可对外口径：定时任务已补齐、结果可自动生成、邮件自动发送已真实打通；QQ 侧仅确认可手动发文件，暂不宣称已自动推 QQ。
- 2026-04-26：日报自动化项目已拆成“抓取/筛选层 + 邮件发送层”两段；已落地 4 个定时任务：`SWS_Report_Run_0740`、`SWS_Report_Run_2110`、`SWS_Report_Send_0810`、`SWS_Report_Send_2130`，用于早晚自动生成和自动发信。
- 2026-04-26：日报规则当前固定为严格 24 小时窗口；数量规则为保底 `12/6/6`、上限 `20/10/10`；两轮补量逻辑已接入，第二轮只补缺口栏目，不使用系统搜索作为主流程。
- 2026-04-26：Gemini 今晚已实测不适合作为日报中文化正式生产链路；中文化改走替代翻译路线，已生成 `daily_report_cn.md` 与 `daily_report_cn_polished.md`，但后者仍需继续清理孤立摘要、孤立来源行和串类条目，明天继续收口。
- 2026-04-27：日报自动化链路（抓新闻 -> 英文原稿 -> 中文稿 -> 发邮件）今天已多次真实跑通，`daily_report_cn.md` 可自动更新并发信；但内容质量修复未完成，主要问题仍是标题中文化不足、摘要模板化严重、国际/财经/科技筛选失真。
- 2026-04-27：今天尝试调 Claude Code / Codex 通过 ACP runtime 协助修稿质量，均失败并报 `ACP runtime backend is currently unavailable`；说明当前 ACP backend 不可用。
- 默认全球综合情报报告的自动抓取已升级为 4 组白名单流程：
  1. `news_core`：BBC、Reuters、AP News、Al Jazeera、CNBC World、Yahoo Finance
  2. `markets_global`：NYSE、TWSE、SSE、JPX、KRX、Investing.com 日本站、Naver Finance、东方财富
  3. `deep_dive`：Reuters Europe、Reuters China、AP Russia-Ukraine、AP China、Yahoo Finance 商品详情页（GC=F / BZ=F / CL=F）
  4. `tech_ai_robotics`：The Verge、TechCrunch、IEEE Spectrum、Wired、Ars Technica、MIT Technology Review、VentureBeat AI
- 默认执行策略已改为：每天 **08:00 / 21:00** 先由 `collect_comprehensive_report.py` 做真实重抓，再于 **08:30 / 21:30** 由 `send_collected_comprehensive_report.py` 发送邮件。
- 这套新版定时任务在 Windows 任务计划程序中的固定任务名为：
  - `SWS_Report_Collect_0800`
  - `SWS_Report_Send_0830`
  - `SWS_Report_Collect_2100`
  - `SWS_Report_Send_2130`
- 报告正文现在默认包含 **AI / 机器人 / 科技前沿** 板块，用来提高科技内容密度。
- 科技板块默认来源固定扩展为：The Verge、TechCrunch、IEEE Spectrum、Wired、Ars Technica、MIT Technology Review、VentureBeat AI、Singularity Hub、AI News、Engadget。
- 自动抓取已加入容错：单组失败不中断整轮报告；运行日志写入 `logs/collect_comprehensive_report.log`，状态写入 `reports/scheduled/latest_collect_status.json`。
- 执行策略：优先走新版 4 组抓取与正式详细版结构；若某板块仍拿不到足够扎实的 24–48 小时更新，继续直接写“今日无重大更新”，不许用旧闻补洞。
- 抓取白名单流程固定为 6 个站点：
  1. Yahoo Finance
  2. AP News
  3. CNBC World
  4. TWSE（辅助校验）
  5. Reuters（按需补抓）
  6. BBC（按需补抓）
- 执行策略：先跑前 4 个高兼容站点，快速生成可用报告；再视需要补抓 Reuters / BBC，避免一开始被 CAPTCHA 与高阻力拖慢整体速度。
- 当用户在 Telegram 中要求“截图给我/把屏幕发我”时，默认使用本地 `telegram-image-sender` 路线：先执行 PowerShell 截图脚本生成 PNG，再在回复中使用 `MEDIA:<本地图片路径>` 直接发送图片；该链路已于 2026-03-25 实测成功。
- 当用户在 Telegram 中要求“打开网页后点第几行第几张图”时，当前可用的半自动路线是：
  1. 先用 `Start-Process` 打开 Google / Bing 图片搜索页
  2. 再用 `telegram-image-sender/scripts/capture-screen.ps1` 截图
  3. 再用 `extensions/desktop-input-control/scripts/screen-ocr.py` + 本机 Tesseract 做本地 OCR 校验页面状态
  4. 点击阶段不要优先直接跑 `desktop-input.ps1`，因为它仍可能触发 AMSI / `ScriptContainedMaliciousContent`
  5. 更稳的做法是用独立内联 `Add-Type` + `SetCursorPos` + `mouse_event` 直接发鼠标点击
  6. 目前“第几行第几张”仍主要靠网格估位，不是精确视觉分块，所以要在点击后再次截图 / OCR，确认是否真的进入了新的图片详情页
- **以后只要启动新项目，默认先提醒大老板：先起项目英文名，再创建新的独立 GitHub 仓库地址，然后再上传。**
- **以后这台机器上传 GitHub，默认优先使用 SSH remote，不走 HTTPS。** 这条规则已在 `global-intel-report-automation` 仓库上传时再次实战确认：HTTPS 会卡在登录对话框并报 `fatal: User cancelled dialog.`，切换到 `git@github.com:...` 后可正常 push。
- 今晚对 `skills/tmall-genie-voice-bridge` 的真实收尾结论也要长期记住：`local_windows_speaker` 旧链路会把 `WMPlayer playState=9` 误当成功，属于**假成功**；以后凡是对外说“Windows 真人语音已打通 / 已能本机出声”，都必须先拿到真实播放证据，不能只看返回码或 state=9。
- 以后我可以默认并行调度 **Codex + Claude Code**：Codex 偏执行和改代码，Claude Code 偏审查、补文档、做第二视角复核；我负责中文沟通、任务拆解、边界控制和最终验收。
- 2026-04-01 大老板进一步明确授权：后续工程任务可以默认由我做**总指挥 / 设计 / 最终验收**，并按需调 `Claude Code` 做代码执行助手；权限上可按“充分执行”口径推进，但仍必须由我控任务边界、真实验收结果和对外表述，不能把执行层输出直接当最终结论。
- 2026-04-01 晚间，大老板又把 **天猫精灵 / `tmall-genie-voice-bridge` 项目** 的协作方式单独钉死：以后这个项目默认由我做 **总指挥 / 设计 / 最终验收 / 最终口径负责人**，并允许我默认调 **Codex CLI** 作为执行助手参与写代码；但所有对外结论、完成度判断与最终验收，仍必须由我统一负责，不能把 Codex 输出直接当结论。
- 2026-03-31 对 `skills/tmall-genie-voice-bridge` 的 90 分钟强攻已确认新的长期结论：
  1. 项目已从“会说的半成品骨架”推进到**可演示 MVP**阶段；
  2. 当前最稳闭环不是现场麦克风，而是：`text -> local speak`、`text -> bridge /speak`、`wav -> transcribe -> echo-speak`；
  3. 本机 `local_windows_speaker` 的 WAV 播放应默认走 `SoundPlayer.PlaySync()`，不能再把 `WMPlayer playState=9` 当真人发声成功；
  4. 已新增并打通的关键入口包括：`speak-local.ps1`、`demo-text-roundtrip.ps1`、`scripts/listen_once.py`、`demo-wav-roundtrip.ps1`、`scripts/check-microphone.ps1`；
  5. 当前机器没有物理麦克风，因此**不能对外宣称“本机麦克风实测已打通”**；下午接上麦后，按 `check-microphone.ps1 -> listen_once.py --timeout-seconds 6 -> --echo-speak` 这条顺序继续验收。
- 2026-03-31 晚间进一步确认：`tmall-genie-voice-bridge` 目前**还未完成真机闭环**，但两条关键桥接层已落地：
  1. 已新增文本回调入口：`POST /callback/text`、`POST /webhook/text`，并支持 `text/query/utterance/message/payload.text/payload.query/intent.query/request.text/request.query` 等字段，说明“后台文本回调路线”已从概念变成当前最现实主线；
  2. 已新增真实设备播放所需的音频 URL 能力：支持 `http_player.audio_base_url = "auto"` 与 `http_player.public_base_url`，说明“bridge 生成音频 -> 暴露可访问 URL -> 外部控制端驱动真机播放”这条路线已补上关键缺口；
  3. 当前最准确项目状态不是“已完成”，而是：**桥接层基本成形，只差真实设备控制端接最后一跳**；
  4. 下一阶段优先级固定为：**Home Assistant -> 阿里技能/云函数/官方开放平台 -> 第三方控制接口**；原始收音继续视为高风险备选，不当主线。 
- 2026-04-05 已确认：OpenClaw v2026.4.2 起，当前 `openclaw-control-ui` / WebChat 路径下的 `exec` 会走新版 **exec approvals** 机制，导致本机命令频繁弹批准条；这不是新闻脚本问题，也不是 `openclaw.json` 里一个显眼的 `approval` 开关。
- 2026-04-05 已实测有效的“关闭审批条 / never prompt”方法如下（用于 gateway 主机）：
  1. 先把 gateway host approvals 改成默认不询问：
     - `openclaw approvals set --gateway --stdin`
     - 内容为：`{ version: 1, defaults: { security: "full", ask: "off", askFallback: "full" } }`
  2. 再把 OpenClaw 请求侧配置对齐：
     - `openclaw config set tools.exec.host gateway`
     - `openclaw config set tools.exec.security full`
     - `openclaw config set tools.exec.ask off`
  3. 最后重启 gateway：`openclaw gateway restart`
- 2026-04-05 验证结果：完成上述 3 步并重启后，`openclaw status` 已可在当前 control-ui 会话中直接执行，不再弹批准条。
- 注意：这套做法等于把本机 `exec` 调成 **full + ask off**，方便但会明显放宽安全边界；若未来要重新收紧，优先从 `openclaw approvals get/set --gateway` 与 `tools.exec.ask/security` 回调。

- 2026-04-28：`skills/nano-banana-bridge` 今天已从“安全骨架 / mock 版”推进到**可真实出图的 OpenAI-compatible 生图插件**：
  1. 已接通 `https://api-cn.hi-code.cc/v1` + `gpt-image-1`，走 `POST /images/generations`；
  2. 已真实验证返回 `data[0].b64_json` 并落本地 PNG，不再只是 mock；
  3. 当前已支持两种调用方式：
     - 显式尺寸：`--size 2048x1152`
     - 比例 + 档位：`--aspect-ratio <ratio> --resolution <1K|2K|4K>`
  4. 当前已支持的 **8 种比例**：`1:1`、`3:2`、`2:3`、`16:9`、`9:16`、`4:3`、`3:4`、`21:9`；
  5. 当前已支持的 **3 种分辨率档位**：`1K`、`2K`、`4K`；
  6. 已真实验证 `16:9 + 2K -> 2048x1152` 可出图成功，并已连续产出垃圾分类项目的外观图、社区场景图、功能流程图；
  7. 当前边界必须继续说清：优先打通的是**文生图**，`input-image` 图生图/编辑分支还没补，`/v1/responses + image_generation` 兼容层也还没补；
  8. 当前最稳的对外使用口径：这条插件链路已经可正式用于学校项目图、比赛展板图、流程示意图等中文场景图生成。

---

## 📚 实用教程合集
### 1. HuggingFace免费云服务器部署教程
#### 服务器配置：2核CPU、16G内存、50GB存储空间（免费）
#### 适用场景：
- 部署演示型Web应用（Gradio/Streamlit/静态站）
- 快速开API/小工具（Docker + FastAPI 等）
- 浏览器里的开发环境（JupyterLab 模板）
- 部署OpenClaw、各类AI服务

#### 部署步骤：
1. 注册HuggingFace账号：<https://huggingface.co/>，完成邮箱验证
2. 点击上方的Space → New Space创建新空间
3. 选择SDK类型（Docker/Python/Node.js等），选择免费套餐
4. 上传项目代码，配置启动命令
5. 开启持久存储（可选）：在设置里升级持久盘，挂载到`/data`目录
6. 配置端口映射和访问权限，即可对外提供服务

---

### 2. codex2gpt部署与使用教程
#### 项目功能：将Codex订阅的GPT-5.4转换为标准OpenAI风格API，供OpenClaw、龙虾Agent等工具调用
#### 核心优势：
- 纯Python标准库实现，无额外依赖
- 提供标准`/v1/responses`接口，兼容所有OpenAI生态工具
- 支持多工具对接，可接入任意工作流、Agent系统

#### 部署步骤：
1. 拉取项目代码，复制`config.example.py`为`config.py`
2. 配置Codex账号信息、服务端口、自定义API密钥
3. 启动服务：`python main.py`
4. 后台常驻：Windows用nssm注册为系统服务，Linux用systemd配置服务
5. 测试接口：调用`http://localhost:8787/v1/responses`验证功能正常

#### 对接OpenClaw：
修改OpenClaw配置文件`config.yaml`，添加模型：
```yaml
models:
  - id: codex-gpt-5.4
    name: GPT-5.4 (Codex)
    provider: openai
    base_url: http://localhost:8787/v1
    api_key: 自定义的API密钥
    default: true
```
重启OpenClaw服务即可使用GPT-5.4作为默认模型。

---

_Last updated: 2026年3月28日_

### 2026年3月28日（夜间补记）
- ✅ 今晚已把 `Codex CLI` 正式接入第三方 OpenAI 兼容模型并跑通，配置路线已确认可用：
  - `C:\Users\besam\.codex\config.toml`
  - `C:\Users\besam\.codex\auth.json`
  - 模型：`gpt-5.3-codex`
  - 接口：`http://92scw.cn/v1`
- ✅ 已做最小真实验收：`codex exec` 成功返回固定文本 `CODEX_ROUTE_OK`，说明 `Codex CLI + gpt-5.3-codex` 已真实可用。
- ✅ 大老板今晚进一步明确新的长期协作方式：以后我默认按**项目经理 / 技术总控 / 最终验收**模式推进，允许我并行调度本地 coding agent；对大老板汇报中文，对新 coding agent 派工优先英文。
- ✅ 新接入的 Codex 已拿 `tmall-genie-voice-bridge` 做了第一轮真实工程压力测试，结论不是摆设：
  - 能读项目、改文件、跑校验；
  - 能自己踩出并修补低风险 bug；
  - 值得继续作为执行层使用，但需要我严格控任务边界，避免改动过宽。
- ✅ `tmall-genie-voice-bridge` 今晚的真实进展已收敛为：
  - mock 链路通过；
  - `bridge_server` 本地 `/health` / `/speak` / `/audio` 链路通过；
  - `local_windows_speaker` 的相对路径解析 bug 已找到并修补；
  - 但**真人语音本机出声仍未打通**：使用 `edge-tts` 做真人声测试时返回 `No audio was received. Please verify that your parameters are correct.`
- ✅ 因此以后对这个项目的对外表述必须继续保持克制：
  - 可以说：mock 链路通、本机播放流程有进展；
  - 不能说：电脑真人语音已确认出声；
  - 更不能说：真实天猫精灵音箱已经成功出声。
- ✅ 明确后续技术顺序：
  1. 先查清 `edge-tts` / 真人语音失败原因；
  2. 先把本机真人语音出声做实；
  3. 再推进真实天猫精灵 / HTTP 播放桥接，不跳步。

### 2026年3月30日
- ✅ 今天在 QQ 私聊实战中，进一步验证了**驱动执行层 AI（尤其 Codex CLI）时的长期方法论**：
  - 我默认扮演**项目经理 / 技术总控 / 最终验收**；
  - 对大老板汇报继续使用中文；
  - 对 Codex 这类执行层 AI，**派工、约束、验收标准优先使用英文**，执行效率和稳定性更高。
- ✅ Windows + PowerShell 环境下调度 Codex CLI 的几个高频坑已经踩实：
  1. 不要迷信复杂 shell 拼接，长 prompt + 重定向很容易翻车；
  2. 长 prompt 可能在 shell / 子进程链路中被拆参，导致 Codex 报 `unexpected argument`；
  3. 后台脚本环境可能继承不到 `codex` 的 PATH，必要时直接用可执行文件绝对路径。
- ✅ 当前更稳的实际调度策略已经明确：
  1. 先做 Codex CLI 最小真测，确认本体可用；
  2. 尽量在**临时副本目录**中执行，避免污染原项目；
  3. 若已进入 Codex 交互界面，优先**直接向现成会话粘贴英文任务**，不要继续折腾外层复杂参数；
  4. 项目经理负责控边界、控口径、控验收，避免执行层 AI 夸大“已完成/已验证”的能力。
- ✅ 这套方法以后默认用于我调度 Codex / 同类 coding agent 的长期协作流程。
- ✅ 今天已按大老板新提供的配置，重新完成一轮 Codex CLI 路由切换并验收通过：
  - 配置文件：`C:\Users\besam\.codex\config.toml`
  - 认证文件：`C:\Users\besam\.codex\auth.json`
  - 新接口地址：`https://www.jnm.lol/v1`
  - 当前模型：`gpt-5.3-codex`
  - 新 API Key：已更新到 `auth.json`（长期记忆中不明文重复展开）
  - 最小真测命令：`codex exec "Reply with exactly: CODEX_ROUTE_OK"`
  - 最小真测结果：成功返回 `CODEX_ROUTE_OK`
- ✅ 结论：当前本机 Codex CLI 走 `https://www.jnm.lol/v1` + `gpt-5.3-codex` 的新路由已真实可用，后续如再切换 Key / base_url，优先沿用“改配置 -> 最小真测 -> 再投入正式任务”的流程。
- ✅ 今晚还已把本机 `Claude Code` 默认模型路由切到同一套 OpenAI 兼容供应方，并完成真实验收：
  - 配置文件：`C:\Users\besam\.claude\settings.json`
  - 正确基地址：`https://www.jnm.lol/`（注意：这里是根地址，不是 `/v1`；Claude Code 会自行拼接 Anthropic 风格路径）
  - 默认模型族：`gpt-5.3-codex`
  - 已同时写入：`ANTHROPIC_DEFAULT_HAIKU_MODEL`、`ANTHROPIC_DEFAULT_OPUS_MODEL`、`ANTHROPIC_DEFAULT_SONNET_MODEL`、`ANTHROPIC_MODEL`、`ANTHROPIC_REASONING_MODEL`
  - 默认权限：`bypassPermissions`
  - 全新进程最小真测命令：`claude -p '只输出：CLAUDE_ROUTE_OK'`
  - 最小真测结果：成功返回 `CLAUDE_ROUTE_OK`
- ✅ 结论：以后若要给 Claude Code 接第三方兼容模型，优先采用“`.claude/settings.json` 全量模型映射 + 根地址 base_url + 全新进程真测”的方法，不要只改单个环境变量，更不要把 Claude Code 的 base_url 误写成 `/v1` 结尾。
