# GitHub 学习雷达（沈万三版）

## 一、定位
GitHub 不是娱乐社区，而是我的**进化训练场**。

我在这里重点学习：
- Skill 设计
- Agent / Workflow 编排
- 自动化落地
- 文档表达与边界定义
- 模板化与产品化

---

## 二、固定学习方向

### 1. Skill / Agent 结构
重点看：
- `README.md`
- `docs/`
- `examples/`
- `prompts/`
- `templates/`
- `scripts/`
- `src/`
- `SKILL.md` 或类似说明文件

我要学的是：
- 输入输出怎么定义
- 任务边界怎么写
- 失败场景怎么处理
- 目录结构怎么组织
- 怎么让别人一看就会用

### 2. 自动化和工作流
重点方向：
- scheduler / cron
- webhook
- browser automation
- desktop automation
- scraping / crawling
- summarization
- notification / alerting
- report generation

### 3. Agent 核心能力
重点关键词：
- `agent`
- `tool calling`
- `memory`
- `rag`
- `retrieval`
- `multi-agent`
- `orchestration`
- `planner`
- `browser use`
- `computer use`

### 4. 产品化能力
重点观察：
- 一个项目怎么从 demo 变工具
- 文档在哪个阶段变完整
- 什么时候开始模板化
- 有没有真实维护与真实使用痕迹

---

## 三、关键词池

### 第一组：当前最相关
- `agent`
- `ai assistant`
- `workflow`
- `automation`
- `tool calling`
- `memory`
- `rag`
- `browser automation`
- `desktop automation`
- `prompt engineering`

### 第二组：和 OpenClaw / Skill 思路贴近
- `plugin`
- `skill`
- `template`
- `persona`
- `system prompt`
- `orchestration`
- `task runner`
- `report automation`

### 第三组：可直接转能力
- `scheduler`
- `webhook`
- `crawler`
- `scraper`
- `summarizer`
- `notification`
- `dashboard`
- `knowledge base`

---

## 四、筛 repo 的标准

### 值得看的 7 条标准
1. 有清晰 README
2. 目录结构不乱
3. 最近有更新
4. 不只是概念，确实有代码
5. issue / discussion 里有人真在用
6. 能看出真实场景
7. 有可迁移价值

### 直接降权的项目
1. 标题吹得太大，代码很空
2. 全是营销话术
3. 只会堆模型名
4. 没文档
5. 长时间不维护
6. 没有明确场景
7. 不能迁移到当前工作里

---

## 五、学习节奏

### 每天：轻巡逻
目标：看趋势，不深挖。

关注：
- 新 repo 标题
- 热门 issue / discussions
- 最近冒头的关键词
- 值得进入候选池的项目

### 每 2~3 天：深读 1~2 个 repo
目标：真正吸收。

固定拆解：
- 它解决什么问题
- 核心结构怎么搭
- 最值得抄的 3 个点
- 哪些是噱头，哪些是真货
- 能否回灌到我的技能体系

### 每周：中文简报
固定结构：
1. 本周新发现
2. 学到的方法
3. 可落地改进
4. 不值得追的坑

---

## 六、每次学习必须回答的 5 个问题
1. 这个 repo 真正解决了什么问题？
2. 它最值得抄的结构是什么？
3. 它的文档哪里写得好？
4. 它的边界和失败场景怎么处理？
5. 我能把哪一部分转成自己的能力？

---

## 七、回灌路径

### 1. 回灌到 skill 模板
- `SKILL.md` 模板
- README 写法
- research 组织方式
- 使用说明模板

### 2. 回灌到工作方法
- 任务拆解方式
- 自动化流程设计
- fallback 设计
- 报告输出结构

### 3. 回灌到可迁移套路
例如：
- 什么任务适合 cron
- 什么任务适合 webhook
- 什么技能必须加 examples
- 什么 agent 要先定义边界再谈人格

### 4. 回灌到风险识别能力
更快识别：
- 什么项目值得学
- 什么是纯包装
- 什么方向热闹但不值得投入

---

## 八、优先关注的 repo 类型

### 第一优先级
- AI agent framework
- prompt / persona / workflow repos
- automation systems
- scraping / monitoring / reporting tools
- memory / RAG / retrieval tools

### 第二优先级
- browser-use / computer-use / desktop-use
- OpenAI-compatible APIs
- plugin / extension systems
- developer toolchains

### 第三优先级
- AI 产品包装类项目
- 展示型 demo
- 热门但实现较浅的项目

---

## 九、硬规则
1. 不追热度，追可迁移性
2. 不看营销文案，先看结构
3. 不迷信 star 数，先看维护质量
4. 不把“新概念”当“新能力”
5. 学完必须总结成方法
6. 学来的东西要能回灌到自己或大老板项目
