
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
- 默认全球综合情报报告的抓取白名单流程固定为 6 个站点：
  1. Yahoo Finance
  2. AP News
  3. CNBC World
  4. TWSE（辅助校验）
  5. Reuters（按需补抓）
  6. BBC（按需补抓）
- 执行策略：先跑前 4 个高兼容站点，快速生成可用报告；再视需要补抓 Reuters / BBC，避免一开始被 CAPTCHA 与高阻力拖慢整体速度。
- 当用户在 Telegram 中要求“截图给我/把屏幕发我”时，默认使用本地 `telegram-image-sender` 路线：先执行 PowerShell 截图脚本生成 PNG，再在回复中使用 `MEDIA:<本地图片路径>` 直接发送图片；该链路已于 2026-03-25 实测成功。

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

_Last updated: 2026年3月25日_
