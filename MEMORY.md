
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
- 2026-04-29：GitHub SSH 上传路线今晚又新增一条必须长期记住的实战结论：**这台机器推 GitHub 仓库时，若 22 端口 SSH 不通，直接切 `ssh.github.com:443`。**
  1. 本次新仓库 `office-productivity-skills` 已真实通过 **SSH 443** 成功上传；
  2. 首次需要先执行：`ssh -T -p 443 git@ssh.github.com`，并确认 `yes`，把 `[ssh.github.com]:443` 写入 `known_hosts`；
  3. 随后把 remote 设为：`ssh://git@ssh.github.com:443/<owner>/<repo>.git`，再执行 `git push -u origin main` 即可；
  4. 本次成功案例：`git@github.com:besam168/office-productivity-skills.git` 因 22 端口链路异常失败，改走 `ssh://git@ssh.github.com:443/besam168/office-productivity-skills.git` 后成功；
  5. 因此以后这台机器的 GitHub 上传默认策略应更新为：
     - **优先 SSH，不走 HTTPS**；
     - **22 端口失败就立刻切 443 SSH，不再死磕**；
     - **第一次只要通过 host key 校验，后面就可复用。**
- 2026-04-29：`office-productivity-skills` 办公插件合集仓库今晚已正式建立并成功上传：
  1. GitHub 地址：`https://github.com/besam168/office-productivity-skills`
  2. 当前仓库已收录：`docx-generator`、`minimax-docx`、`minimax-xlsx`、`pptx-generator`、`word-to-pdf`
  3. 已包含中文安装教程：`docs/install-guide-zh.md`
  4. 以后若另一台 OpenClaw 电脑要补 Office 能力，优先直接从这个仓库拉取，不再从总工作区临时拼装。
- 2026-05-07：大老板今天已明确要求把“生图 + 做 PPT”这套能力正式沉淀到长期记忆。以后默认正式口径固定为：
  1. 生图正式插件：`ppt-image-bridge`
  2. 默认模型：`gpt-image-2`
  3. 正式主链路：`https://api-cn.hi-code.cc/v1/images/generations`
  4. 默认目标：**真2K优先**
  5. 横版默认真2K：`2048x1152`
  6. 当前已真实成功打通一次：`ppt-image-bridge + gpt-image-2 + 2048x1152`，成图文件：`skills/ppt-image-bridge/output/stable-image_20260507_094712.png`
  7. 以后大老板在聊天里只要说：`生图`、`给PPT配图`、`图也一起做`，默认优先理解为：`ppt-image-bridge -> gpt-image-2 -> 真2K优先`，不再优先回退旧的低分辨率稳态口径。
  8. 做 PPT 时默认同步记住：图是真2K不等于进 PPT 就一定好看，交付时还要一起控制图框比例、contain/cover、封面裁切、留白和标题位置。
  9. 当前给别人直接复用的标准说明书固定为：`C:\Users\besam\.openclaw\workspace\手机端生图做PPT教程_正式可复制版.md`，不要再优先发旧的示例口令版。
- 2026-04-30：大老板已明确新的默认口径：**以后在聊天里只要说“美股”或“美股指数盘面”，默认就是查“真指数”，不是ETF代理。**
  1. 默认查询对象固定为：
     - `^DJI` = 道琼斯工业指数
     - `^IXIC` = 纳斯达克综合指数
     - `^GSPC` = 标普500指数
  2. **不得再把 `SPY / QQQ / DIA` 直接说成三大指数**；它们最多只能作为 ETF 代理或情绪参考，且必须明确标注“ETF”。
  3. 默认输出顺序固定为：
     - 三大真指数点位与涨跌幅
     - 一句盘面判断（强 / 弱 / 分化 / 震荡）
     - 如有需要再补七巨头或科技权重
  4. 若系统桥接文件 `reports/scheduled/qveris_market_snapshot.json` 无效、过期、缺核心键，**不得拿缓存硬回**；应直接切到可用实时行情链路。
  5. 当前可用的严格查询口径，优先使用能返回真指数的实时工具，不再优先用 ETF 替代指数。
  3. `https://api-cn.hi-code.cc/v1` 的 `/responses + image_generation` 当前会退化成普通文本响应（返回 `tools: []`、`tool_choice: none`），说明这条兼容层**不能把 Responses 当正式生图路径**；
  4. 因此当前生产用法应明确收敛为：**只走 `--api-mode images`，不走 `auto` / `responses` 作为正式口径**；
  5. 今天已真实成功出图的稳态参数组合包括：
     - `--size 1536x1024`
     - 简单、收敛的中文 prompt
     - 单次 1 张
     - 输出文件落在 `skills/nano-banana-bridge/output/`
  6. 今日实测成功样例：
     - 社区手绘场景图已成功生成：`nano-banana_20260429_162355.png`
     - 请求 `4096x4096` 虽返回成功，但上游实际回落为 `1024x1024`，说明**当前不能把“请求 4K”当作“真实 4K 已实现”**；
  7. 当前最准确对外口径：
     - **已修复到可稳定出图（以 1536x1024 这一档最稳）**；
     - **假 4K / 自动降级尺寸仍需继续观察**；
     - 若要正式生产，优先先出稳图，再考虑后续超分或更高分辨率路线。
- 2026-04-28：`skills/nano-banana-bridge` 现在已不是纯 mock 骨架，而是已接通真实生图链路：
  1. 当前已验证的 provider 路线为：`openai-compatible` + `https://api-cn.hi-code.cc/v1` + `gpt-image-1`；
  2. 已支持两种主要调用写法：`--size <宽x高>` 与 `--aspect-ratio <比例> --resolution <1K|2K|4K>`；
  3. 已支持 8 种比例：`1:1 / 3:2 / 2:3 / 16:9 / 9:16 / 4:3 / 3:4 / 21:9`；
  4. 今晚新增踩实的关键经验：这条链最稳的不是“随便调”，而是**单张 + 简单 prompt + 显式真尺寸**，尤其 `--size 2048x1152` 已真实成功落图；
  5. 复杂 prompt、连续多次不同参数调用更容易触发 `HTTP 502 / upstream_error`，因此当前正式生产口径应优先采用“窄而稳”的调用路径；
  6. `skills/nano-banana-bridge/USAGE_ZH.md` 已存在中文教程，后续优先按教程与这条成功基线复用，不要每次从 0 试错。
- 2026-04-28：`skills/auction_915_925_smooth_scanner_v2` 今天已完成真正收口：
  1. 原先只挂上 `沈万三_集合竞价狙击手V2_0915_Capture`，缺少 `沈万三_集合竞价狙击手V2_092430_Judgement`，已重新执行安装脚本补齐两阶段任务；
  2. 已成功生成当日正式产物：`auction_sniper_v2_20260428.csv/.json/.md`，并补做 `auction_sniper_v2_20260428_excel.xlsx`；
  3. 今日 V2 命中 5 只票并已人工核准名称：众生药业、恒润股份、圣阳股份、崇达技术、美利云；
  4. 已新增 `scripts/send_v2_mail.py`，并把 `run_judgement_092430.py` 接成“判定成功后自动发邮件”，实测返回 `MAIL_SENT_OK`；
  5. 当前 V2 可对外口径：定时任务已补齐、结果可自动生成、邮件自动发送已真实打通；QQ 侧仅确认可手动发文件，暂不宣称已自动推 QQ。
- 2026-04-26：日报自动化项目已拆成“抓取/筛选层 + 邮件发送层”两段；已落地 4 个定时任务：`SWS_Report_Run_0740`、`SWS_Report_Run_2110`、`SWS_Report_Send_0810`、`SWS_Report_Send_2130`，用于早晚自动生成和自动发信。
- 2026-04-26：日报规则当前固定为严格 24 小时窗口；数量规则为保底 `12/6/6`、上限 `20/10/10`；两轮补量逻辑已接入，第二轮只补缺口栏目，不使用系统搜索作为主流程。
- 2026-05-07：大老板已明确新的默认动作：以后在聊天里只要说 **“跑龙股”**，我就默认调用 `skills/pivot_open_signal_scanner` 这条 `Shakeout Dragon Capture / 异动倍量·洗盘擒龙战法` 插件链路。
  1. 本次真正把它从“偶尔能跑”推进到“可用”的关键原因，不是单点策略，而是工程链路一起收口：
     - 名称解析改成：**腾讯行情优先 + 东方财富兜底 + 本地映射表兜底**；
     - 历史日线抓取加了**超时保护**，避免单票拖死整轮；
     - 新增 **fast-mode**，大池子时优先只打首选 server，并把 `history_timeout_sec` 压短；
     - `run_relaxed.py` 已支持参数透传，可直接跑：`--limit 1500 --fast-mode --history-timeout-sec 0.6`。
  2. 2026-05-07 早上这轮已真实确认：
     - 用 **1500 股票池** 跑放宽版成功落盘；
     - 生成时间：`2026-05-07 07:07:02`；
     - 参数：`limit=1500`、`fast_mode=True`、`history_timeout_sec=0.6`、`min_up_days=3`、`min_volume_multiple=1.7`、`post_avg_vol_ratio_max=0.85`；
     - 本轮 `passed_count=63`，说明**能出票**，但更像“大网初筛”，不能直接当最终实盘名单。
  3. 因此以后默认流程固定为两段：
     - **第一段：大网初筛** → 跑放宽版，先把候选池筛出来；
     - **第二段：重点观察名单** → 再按弹性、量能、非 ST、辨识度收缩成 **10~20 只**。
  4. 当前默认压缩方法：
     - 优先看 `last_close / base_price` 的弹性；
     - 再看 `signal_volume` 的量能级别；
     - **ST / *ST 默认降权或剔除**，除非大老板明确要看；
     - 文件里名字若显示正常、终端里像乱码，优先信文件 UTF-8 内容，不要误判成产物损坏。
  5. 这次 1500 池放宽版收缩后的重点观察名单，可作为以后“跑龙股”后的第一版交付样式参考：
     - 恒申新材
     - 联发股份
     - 锦和商管
     - 展鹏科技
     - 龙星科技
     - 快意电梯
     - 奥拓电子
     - 超讯通信
     - 双象股份
     - 福日电子
     - 炜冈科技
     - 拓山重工
     - 惠威科技
     - 至纯科技
     - 瀛通通讯
     - 香溢融通
     - 雅运股份
     - 乐通股份
  6. 当前对这条插件的最准确长期口径：
     - **已具备“跑龙股”可用性**；
     - **已验证 1500 池可出票**；
     - 但第一轮原始候选常常偏多，默认必须做二次收缩，不直接把大网筛结果当最终答案。
- 2026-04-27：日报自动化链路（抓新闻 -> 英文原稿 -> 中文稿 -> 发邮件）今天已多次真实跑通，`daily_report_cn.md` 可自动更新并发信；但内容质量修复未完成，主要问题仍是标题中文化不足、摘要模板化严重、国际/财经/科技筛选失真。
- 2026-04-30：日报自动化项目今天已与“全球综合情报长报告链”正式切分清楚；当前应长期记住两条线不是一回事：
  1. **日报自动化项目**：`run_daily_report.py` -> `generate_daily_report_cn.py` -> `send_daily_report_cn.py`
  2. **全球综合情报长报告链**：`collect_comprehensive_report.py` / `send_collected_comprehensive_report.py`
- 2026-04-30：今天已按大老板要求真实跑通日报自动化项目的“生成 + 发送”全链：
  - `run_daily_report_openclaw.bat` 生成成功
  - `run_send_daily_report_cn.bat` 返回 `SENT_OK`
  - 当前规则仍是严格 24 小时窗口，因此邮件主体主要是前一日（2026-04-29）新闻，不等于“发旧邮件”，但也不能夸大成“完全全新当天内容”。
- 2026-04-30：日报自动化项目的 Windows 任务计划程序今天已正式切换完成并验收通过：
  - 已禁用旧任务：`\OpenClaw\DailyNewsReport_AM_0735`、`\OpenClaw\DailyNewsReport_PM_2105`
  - 已启用新任务：`\SWS_Report_Run_0740`、`\SWS_Report_Run_2110`、`\SWS_Report_Send_0810`、`\SWS_Report_Send_2130`
  - 今日已真实看到：`\SWS_Report_Run_0740` 与 `\SWS_Report_Send_0810` 成功执行
- 2026-04-30：大老板今天新增并确认一条长期口径：**这条日报自动化项目的报告署名以后统一用 `整理：Wsws168`。**
- 2026-05-07：大老板再次明确并要求长期记住新的生图默认口径：
  1. **以后默认生图优先使用 `gpt-image-2`**，不再默认先走 `gpt-image-1`；
  2. **以后默认优先要“真 2K”**，不能把 `1536x1024` 这类稳态高分档说成严格真2K；
  3. 当前横版真2K最明确、应优先复用的默认尺寸继续固定为：`2048x1152`（即 `16:9 + 2K`）；
  4. 以后只要大老板直接说“生图”，默认理解为：`ppt-image-bridge` + `gpt-image-2` + 真2K优先；
  5. 如果因为 provider 波动、比例不稳或失败而降级尺寸，必须明确告诉大老板是“降级到稳态尺寸”，不能把非真2K冒充成真2K。
  6. 2026-05-07 当天进一步完成了 `ppt-image-bridge` 的真2K扩展与实测收口：
     - 脚本已纳入的真2K尺寸组：`2048x1152`、`1536x1536`、`1152x1536`、`2048x1448`、`1448x2048`
     - **已真实测通并可优先复用**：`2048x1152`（16:9）、`1536x1536`（1:1）、`1152x1536`（9:16）
     - **已放入脚本但本轮未打通、当前仍需观察**：`2048x1448`（3:2）、`1448x2048`（2:3），本轮实测均返回 `HTTP 502 / upstream_error`
     - 因此长期口径必须继续克制：**脚本已支持 ≠ provider 已稳定打通**；只有真实成功返回的尺寸，才能对外说“已测通”。
- 2026-05-07：今天“华为汽车 / 鸿蒙智行”PPT + 生图协同链路又形成了一套值得长期复用的方法：
  1. **做高端 PPT 时，不能只盯生图质量，还必须同步控制 PPT 图框比例**；这次已验证：原图即使是标准 `2048x1152` 真2K 16:9，只要 PPT 内图框不是严格 16:9，视觉上仍会出现变形、留边或被错误裁切；
  2. 以后凡是往 PPT 里插横版主视觉图，默认优先使用 **严格 16:9 图框**；封面可用 `cover` 裁切，但图框本身仍必须是 16:9；内页图若不想裁切失真，优先走 16:9 安全框；
  3. 这次已正式形成两档可复用交付方向：
     - **视觉路演版**：更像高端品牌发布会，黑 / 米白 / 酒红，少字、强节奏、重氛围；
     - **咨询公司终稿版**：更短、更硬、更整齐，每页一句核心判断，更像老板过会材料；
  4. 以后大老板如果说“把图插件入 PPT，还要欧洲风格、惊艳视觉”，默认理解为：**先用 `gpt-image-2` 按真2K出图，再按 Expert Designer 思路收成高端欧洲审美版式**，而不是只把图机械塞进页里；
  5. 这次“咨询公司终稿版”的可复用成品与脚本已落地：
     - 脚本：`skills/pptx-generator/scripts/render_huawei_european_showcase_consulting.js`
     - 成品：`skills/pptx-generator/output/huawei-auto-consulting-final.pptx`
     - 相关视觉增强版：`skills/pptx-generator/scripts/render_huawei_european_showcase_v2.js`
     - 相关视觉增强版成品：`skills/pptx-generator/output/huawei-auto-european-showcase-v2.pptx`
  6. 这类活以后默认工作顺序应固定为：**先定风格口径 -> 再按真2K生图 -> 再校正 PPT 图框比例 -> 最后收两版（视觉版 / 终稿版）**，不要跳步。
- 2026-04-30：今天已把这条日报自动化项目收成独立 GitHub 仓库，作为以后换系统/换电脑的迁移基础：
  1. 仓库名：`global-news-mail`
  2. GitHub：`https://github.com/besam168/global-news-mail`
  3. 本地目录：`C:\Users\besam\.openclaw\workspace\global-news-mail`
  4. SSH remote：`ssh://git@ssh.github.com:443/besam168/global-news-mail.git`
  5. 首次提交：`d1d4f16` — `Initialize global-news-mail repo skeleton`
- 2026-04-30：当前对 `global-news-mail` 的最准确长期口径必须克制：
  - **已完成第一版仓库骨架、脚本归档、任务脚本与中文教程上传**；
  - **还不能说“第二台电脑拉下来就 100% 即装即用”**；
  - 下一轮要继续补：依赖自描述、配置统一、仓库内独立真跑验收。
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

- 2026-04-30：今天“生图”这条口径已再次正式收口，后续必须默认这样执行：
  1. 只要大老板在聊天里直接说 **“生图”**，默认优先启动 **`skills/ppt-image-bridge`**，不要再先绕回默认 `image_generate`，也不要先走花哨映射路线；
  2. 当前正式默认链路固定为：`openai-compatible` + `https://api-cn.hi-code.cc/v1` + `gpt-image-1` + `POST /images/generations`；
  3. 当前正式默认尺寸优先用稳定三档：`1024x1024` / `1536x1024` / `1024x1536`；其中竖图默认优先 `1024x1536`；
  4. `https://www.hi-code.cc/v1` 今天再次实测确认会触发 Cloudflare `HTTP 403 / Error 1010 / browser_signature_banned`，因此**不得再当默认正式入口**；
  5. 今天新建并收口的正式稳版插件对外名与工作区目录现已统一为：`ppt-image-bridge`；当前目录：`skills/ppt-image-bridge/`；核心脚本为：`scripts/generate_image_stable.py`；
  6. 这条新稳版插件今天已真实跑通并成功出图：
     - 输出文件：`skills/ppt-image-bridge/output/stable-image_20260430_151616.png`
     - 实测成功参数：`api-cn.hi-code.cc/v1` + `gpt-image-1` + `1024x1536` + `b64_json`
  7. 今日已把这条插件独立收成 GitHub 仓库：
     - 仓库名：`ppt-image-bridge`
     - GitHub：`https://github.com/besam168/ppt-image-bridge`
     - SSH remote：`ssh://git@ssh.github.com:443/besam168/ppt-image-bridge.git`
     - 首次提交：`388ce06` — `Initialize ppt image bridge`
  8. 今日又把 Images 2.0 / `gpt-image-2` 测试线独立收成实验仓：
     - 仓库名：`ppt-image-bridge-v2-lab`
     - GitHub：`https://github.com/besam168/ppt-image-bridge-v2-lab`
     - SSH remote：`ssh://git@ssh.github.com:443/besam168/ppt-image-bridge-v2-lab.git`
     - 首次提交：`cb7477c` — `Initialize ppt image bridge v2 lab`
  9. 当前这两仓的默认分工必须长期记住：
     - **`ppt-image-bridge`** = 正式生产仓，默认稳定出图、PPT 配图、中文说明图与日常交付优先走这条；
     - **`ppt-image-bridge-v2-lab`** = Images 2.0 / `gpt-image-2` 实验仓，专门测试中文排版、2K/4K、多比例与新能力，不默认代替正式版；
  10. 截至 2026-04-30 今日已真实踩实的 `gpt-image-2` 2K 可用比例包括：
     - `1:1 + 2K` → `2048x2048`
     - `16:9 + 2K` → `2048x1152`
     - `9:16 + 2K` → `1152x2048`
     - `3:2 + 2K` → `2304x1536`
     - `2:3 + 2K` → `1536x2304`
     当前失败/不稳：`16:9 + 4K`、`21:9 + 2K`、`4:3 + 2K`、`3:4 + 2K`；以后必须按真实测试结果说话，不能按请求尺寸夸口。
  11. 以后对大老板的执行纪律也要固定：**不要再把命令丢给大老板手动折腾**；默认由我直接接管生图链路、调试、测试分仓与口径控制。

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

- 2026-04-29：大老板已明确新增一条长期工作规则：**以后只要他说“美股情报”，我就默认优先调用 `skills/tradingagents-bridge` 来做美国市场情绪/方向分析，并直接按“中文市场情报简报”口径输出。**
  - 默认优先查看代表性标的：`SPY`（标普）、`QQQ`（纳指科技），需要时补 `DIA`（道指）以及核心个股如 `NVDA / AAPL / TSLA`；
  - 默认先给“简版盯盘口径”（偏多/偏空、risk-on/risk-off、科技强弱、进攻还是防守），若大老板要“详细版”，再补更完整分析；
  - 当前已确认的一次实战口径：2026-04-29 用 `tradingagents-bridge` 查 `SPY / QQQ` 后，判断为 **美股情绪偏多、风险偏好回升、科技偏强、市场更偏进攻端**；
  - 以后听到“美股情报”，默认直接进入这个流程，不再反复确认插件名。
- 2026-04-29：大老板又明确补充一条长期工作规则：**以后凡是我生成的 Office 文件（如 PPTX / DOCX / XLSX / PDF 等可发送文件），默认直接通过 QQ 用 `<qqfile>` 发过去，不要只报本地路径、也不要等大老板再提醒。**
- 2026-05-06：`skills/pivot_open_signal_scanner` / `Shakeout Dragon Capture` 这一轮项目已被大老板明确要求暂停，当前停点与后续续工口径固定如下：
  1. 主线已推进三条线：名字修正、双预设入口、历史日线稳定性；
  2. 已落地双入口：`pipeline/run_strict.py`、`pipeline/run_relaxed.py`；已知关键提交包括：`66020ad2`（`Add shakeout strict and relaxed runners`）与 `f674df6e`（`Try Eastmoney name fallback for shakeout scanner`）；
  3. 首轮有效验收基线结果：
     - 放宽版 `run_relaxed.py`：`passed_count=5` → `sh600993`、`sh603690`、`sh603915`、`sz002216`、`sh600203`
     - 严格版 `run_strict.py`：`passed_count=4` → `sh600993`、`sh603690`、`sz002216`、`sh600203`
  4. 名称修复主结论：多数股票名称在产物层（尤其 JSON）已恢复正常中文；当前问题不应再笼统表述成“名字没取到”或“文件写坏了”。
  5. 当前真正未收口的主问题已收敛为：**历史日线抓取阶段的运行期阻塞 / 稳定性不足**。项目不是“必死”，而是“有时能过、有时会卡”；更像 `pytdx` 历史日线请求、单票拉取超时/熔断不足导致的偶发卡死。
  6. 若后续重启这条项目，默认不要再从名字乱码泛查开始，而应直接从这两点接上：
     - 先补历史日线抓取阶段的超时、单票失败跳过与熔断；
     - 再做短窗口复跑验收，并继续以首轮有效结果（5/4 只）做对照基线。

- 2026-05-05：新的语音主项目今天已正式立项：
  1. 英文仓库名：`voice-agent-mvp`
  2. 中文名：**阿三语音**
  3. 项目定位：**电脑端实时语音对答主引擎**，不是从天猫精灵真机闭环重新开搞；
  4. 与旧项目关系固定为：
     - `voice-agent-mvp / 阿三语音` = 主项目，先做本体；
     - `tmall-genie-voice-bridge` = 后续桥接层，等本体成熟后再接入智能音箱/天猫精灵。
- 2026-05-05：阿三语音第一阶段目标也已固定：
  1. 手动开始录音
  2. 用户说一句
  3. STT 转文字
  4. LLM 生成回复
  5. TTS 播放回复
  - 第一阶段验收标准：**一句输入 -> 一句语音回答**
  - 第一阶段明确先不做：唤醒词、常驻监听、VAD 自动截断、可打断、完整状态机、天猫精灵真机接入。
- 2026-05-05：阿三语音今天已完成第一轮工程骨架搭建：
  - 已新建 `voice-agent-mvp/`、`config/`、`scripts/`、`output/`、`docs/`
  - 已写入基础文件：`README.md`、`config/config.example.json`、`docs/install-guide-zh.md`
  - 已建立首批脚本：`record_audio.py`、`transcribe_audio.py`、`ask_llm.py`、`synthesize_tts.py`、`play_audio.py`、`run_voice_roundtrip.py`
- 2026-05-05：阿三语音今天的关键技术策略也要长期记住：
  1. 第一轮优先先做**音频底座**，顺序固定为：先录音，再播放，再往上接 STT / LLM / TTS；
  2. 当前本机未安装可直接起步的 Python 录音/STT 关键包（`sounddevice` / `pyaudio` / `speech_recognition` / `whisper` / `faster_whisper` 均未就绪），因此首轮更适合优先复用本机已踩实的 ffmpeg / PowerShell / 旧项目脚本链路；
  3. 已决定复用 `tmall-genie-voice-bridge` 的稳定 WAV 播放经验：`play_audio.py` 调 `play-local-audio.ps1`，避免重复踩“假成功播放”老坑；
  4. `record_audio.py` 第一版已按 `ffmpeg + dshow + 16kHz 单声道 + Logi C270 麦克风` 方向落地。
- 2026-04-29：关于“美股情报”产物形式，又新增一条长期经验：**如果大老板要更直观的 Office 产物，优先做“图表化的一页版或两页版”而不是长文字。**
  - Excel 优先做：**一页看板 + 竖向柱状图**，上面放一句话结论/最强四只/市场风格，下面放数据表；
  - PPT 优先做：**两页版**，第一页总览 + 柱状图，第二页分组/占比/盯盘建议；
  - 以后遇到类似“10只股票对比/强弱排行/一句话点评”，优先按这种更直观、更有颜色层次的模板出 Office 文件。

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

- 2026-05-06：今天正式把“Claude Design / Expert Designer”这条设计增强路线落进本地工作区，形成可持续复用的设计模式，而不再只停留在聊天提示词层。
  1. 已新建本地项目目录：`design-expert-mode/`
  2. 已落地核心文件：
     - `design-expert-mode/README.md`
     - `design-expert-mode/expert-designer-prompt.md`
     - `design-expert-mode/style-presets.md`
     - `design-expert-mode/delivery-checklist.md`
     - `design-expert-mode/usage.md`
  3. 已把外部 gist `claude_design_system_prompt.md` 的高价值方法论吸收进本地 prompt，并补了融合说明：
     - `design-expert-mode/gist-integration-notes-2026-05-06.md`
  4. 当前最准确口径：
     - **已完成第一版本地骨架与 gist 精华融合**；
     - **还没到“完整自动化设计代理”程度**；
     - 当前更像一套“沈万三在设计任务里默认启用的专家级设计工作模式”。
  5. 这套模式当前覆盖范围：
     - PPT 设计
     - 网页 / Landing Page 设计
     - UI / UX 页面结构
     - 原型草图
     - 海报 / 封面 / 信息图
  6. 当前已明确的设计工作方法应长期记住：
     - 用户是经理，我是设计执行负责人；
     - 设计任务优先交付“结构 + 版式 + 视觉节奏”，不只交文案；
     - 适合预览时优先 HTML/CSS 高保真稿；
     - 设计前优先吸收现有上下文（品牌、截图、代码、模板、参考页）；
     - 避免 filler content、廉价 AI 俗套、乱堆元素；
     - 多版本探索优先做 variation / tweak，而不是散乱开很多份稿；
     - 交付前必须做 checklist 自检。
  7. 已追加一条很实用的迁移要求：以后如果另一台电脑也要复用这套模式，优先直接复制 `design-expert-mode/` 目录，并按中文教程启用，不要重新口头解释一遍。
  8. 已新增教程文件（供另一台电脑迁移使用）：
     - `design-expert-mode/EXPERT_DESIGNER_另一台电脑迁移教程.md`
  9. 这条线后续最优先实测样本，固定为昨天的 PPT 项目：
     - `skills/pptx-generator/output/linzeqi-totoro-finished.json`
  10. 后续默认执行顺序：
     - 先记忆和教程沉淀
     - 再拿真实 PPT / 网页项目做 Expert Designer 增强版实测

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
