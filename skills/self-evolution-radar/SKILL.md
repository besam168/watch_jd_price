---
name: self-evolution-radar
description: |
  与实际工作结合的自我进化技能。适用于当用户想把真实工作里暴露的
  搜索、抓取、skill、自动化、执行顺序等卡点，当场补成脚本 / skill /
  模板 / 工作流，并在需要时用 Reddit 和 GitHub 做外部巡逻、找实现、
  找可回灌方法时使用。
---

# self-evolution-radar

当用户想做以下事情时，使用本 skill：

- 在真实工作里发现卡点后，当场补能力缺口
- 把一次问题处理沉淀成脚本 / skill / 模板 / 工作流
- 巡逻最近 AI / Agent / 自动化 方向有什么值得借鉴的新东西
- 从 Reddit 看社区热点、真实痛点、用户情绪
- 从 GitHub 找对应的实现、候选 repo、可迁移的方法
- 做一轮“与当前工作绑定”的外部学习雷达 / 研究巡逻 / 技术侦察
- 生成一份面向当前项目的“可回灌建议”

一句话：

**真实工作里发现卡点 → 当场解决 → 沉淀成脚本 / skill / 模板 / 工作流 → 下次更稳、更快、更强。**

## 这个 skill 的定位

这不是成熟的全自动研究平台，也不是只负责“外部巡逻”的信息收集器。

当前更准确的定位是：

**一个与实际工作绑定的自我进化 skill 原型。**

它的目标不是承诺全自动高质量研究闭环，而是：
- 在真实工作里发现卡点
- 尝试当场补洞
- 需要时再用外部巡逻找方法与实现
- 最终把结果沉淀成可复用能力

## 当前能力边界

### 已具备
- 明确的巡逻方向与观察范围
- Reddit / GitHub 双引擎分工
- 方法文档与执行清单
- 最小真实抓取脚本
- 可产出一轮原始巡逻结果
- 可同步生成一份结构化 Markdown 巡逻摘要

### 尚未具备
- 完整参数化配置
- 自动打分与自动排序
- 自动深读 repo
- 自动抽取评论高频痛点
- 自动周报/日报
- 稳定调度与日志体系
- 完整历史归档与趋势对比

因此，对外表述必须克制：

### 可以说
- 能做一轮 Reddit + GitHub 外部巡逻
- 能输出热点、候选 repo、回灌方向
- 能作为研究与学习雷达的 V1 原型

### 不能说
- 不能说已经是成熟产品
- 不能说已经实现全自动研究闭环
- 不能说已经具备完整平台级调度和分析能力

## 默认工作流

1. 先看真实工作里这次卡点是什么
   - 搜索不稳
   - 抓取不稳
   - 某个 skill 卡点
   - 自动化链路不稳
   - 执行步骤过于依赖临场运气
2. 能当场补洞的先补洞
   - 补脚本
   - 补备用路径
   - 补模板
   - 补 skill
   - 补更稳的执行顺序
3. 需要外部输入时，再看 Reddit / GitHub
   - Reddit 看热点、痛点、情绪、争议点
   - GitHub 看实现、结构、README、维护痕迹
4. 做第一轮筛选
   - 值得深读
   - 仅观察
   - 噪音方向
5. 形成回灌结论
   - 哪些方法值得迁移
   - 哪些结构可以抄
   - 哪些坑应该避开
   - 如何沉淀成下次更稳的工作流

## 输出建议结构

默认优先输出以下结构：

1. **本轮巡逻主题**
2. **Reddit 热点与用户痛点**
3. **GitHub 候选项目 / 候选方向**
4. **值得深读的 3 个重点**
5. **对当前项目可回灌的方法**
6. **不建议追的噪音方向**
7. **下一步建议动作**

## 使用原则

### 1. 不做“只摘链接”的空巡逻
结果必须有判断，不只是堆网页。

### 2. 默认围绕当前项目与能力带
优先关注这些方向：
- AI agent framework
- workflow / orchestration
- memory / RAG / retrieval
- browser automation
- desktop automation
- prompt / persona / template
- report / monitor / summary pipeline

### 3. 先给可用结论，再扩展材料
如果时间有限，优先给：
- 值得关注什么
- 为什么值得关注
- 对当前项目有什么帮助

### 4. 不夸大自动化能力
若本轮只是最小抓取 + 人工筛选，就明确说清楚。

## 脚本与参考资料

### 脚本
- `scripts/run_real_patrol.py`
  - 当前最小真实巡逻脚本
  - 用于抓取部分 Reddit RSS 与 GitHub topic 页面
  - 当前已支持参数：`--topic`、`--source`、`--reddit-limit`、`--github-limit`、`--output`
  - 默认会同时生成：原始巡逻文本 + 结构化 Markdown 摘要
  - 新增参数：`--summary-output`、`--no-summary`

### 参考文档
- `references/README.md`
- `references/first-real-patrol-v1.md`
- `references/execution-checklist.md`
- `references/watchlist.md`
- `references/reddit-radar.md`
- `references/github-learning-radar.md`
- `references/learning-log.md`
- `references/SELF-EVOLUTION-TUTORIAL.md`

## 最小运行口径

在需要拉一轮真实素材时，可运行脚本：

```powershell
python .\skills\self-evolution-radar\scripts\run_real_patrol.py
```

也支持参数化调用，例如：

```powershell
python .\skills\self-evolution-radar\scripts\run_real_patrol.py --topic agent --source both --reddit-limit 5 --github-limit 10
python .\skills\self-evolution-radar\scripts\run_real_patrol.py --topic browser-automation --source github --github-limit 15
python .\skills\self-evolution-radar\scripts\run_real_patrol.py --topic openclaw --source both --output .\skills\self-evolution-radar\patrol-openclaw.txt
```

当前内置 topic preset 包括：
- `general`
- `agent`
- `browser-automation`
- `memory`
- `openclaw`

运行成功后，应生成一份文本结果文件，供人工筛选与后续总结使用。

默认还会额外生成一份 Markdown 摘要，结构包含：
- 本轮巡逻主题
- Reddit 热点与用户痛点
- GitHub 候选项目 / 候选方向
- 值得深读的 3 个重点
- 可回灌方法
- 噪音方向
- 下一步建议动作

## 验收标准

一次合格的 skill 输出，至少要满足：

- 不只是贴链接
- 能区分“热点 / 候选 / 噪音”
- 能指出至少 2-3 个可回灌点
- 能明确说明本轮边界与不确定性
- 不把原型能力吹成成熟平台
