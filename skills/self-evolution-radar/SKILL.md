---
name: self-evolution-radar
description: |
  外部学习巡逻与研究雷达技能。适用于当用户想从 Reddit 和 GitHub
  做一轮 AI / Agent / 自动化 / memory / browser automation 等方向的
  外部情报扫描、学习巡逻、候选项目筛选、方法回灌总结时使用。
---

# self-evolution-radar

当用户想做以下事情时，使用本 skill：

- 巡逻最近 AI / Agent / 自动化 方向有什么值得关注的新东西
- 从 Reddit 看社区热点、真实痛点、用户情绪
- 从 GitHub 找对应的实现、候选 repo、可迁移的方法
- 做一轮“外部学习雷达 / 研究巡逻 / 技术侦察”
- 生成一份面向当前项目的“可回灌建议”

一句话：

**Reddit 提题，GitHub 解题，最后回灌到当前项目。**

## 这个 skill 的定位

这不是成熟的全自动研究平台。

当前更准确的定位是：

**一个可复用的双引擎外部巡逻 skill V1。**

它的目标是帮助操作者建立稳定的外部学习工作流，而不是承诺全自动高质量研究闭环。

## 当前能力边界

### 已具备
- 明确的巡逻方向与观察范围
- Reddit / GitHub 双引擎分工
- 方法文档与执行清单
- 最小真实抓取脚本
- 可产出一轮原始巡逻结果

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

1. 先识别本轮巡逻主题
   - 如：AI agents、browser automation、memory、OpenClaw skills、workflow automation
2. 先看 Reddit 侧信号
   - 最近热帖
   - 高频话题
   - 用户真实痛点
   - 情绪和争议点
3. 再看 GitHub 侧实现
   - 对应 topic / repo
   - README 是否清晰
   - 目录结构是否值得学
   - issue / discussions 是否有真实使用痕迹
4. 做第一轮筛选
   - 值得深读
   - 仅观察
   - 噪音方向
5. 形成回灌结论
   - 哪些方法值得迁移
   - 哪些结构可以抄
   - 哪些坑应该避开
   - 对当前项目下一步有什么帮助

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

运行成功后，应生成一份文本结果文件，供人工筛选与后续总结使用。

## 验收标准

一次合格的 skill 输出，至少要满足：

- 不只是贴链接
- 能区分“热点 / 候选 / 噪音”
- 能指出至少 2-3 个可回灌点
- 能明确说明本轮边界与不确定性
- 不把原型能力吹成成熟平台
