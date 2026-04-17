# Self-Evolution Long-Term Memory Layer (SE-LTM Layer)

> 中文名：**自我进化长期记忆层**
> 
> 用途：为 `self-evolution` 提供一个**长期可积累、可检索、可回看、可升级** 的记忆层。这里不是单次对话缓存，而是自我进化过程的长期资产层。

---

## 为什么一定要有 SE-LTM Layer

如果没有这层，`self-evolution` 很容易退化成：
- 每次都重新想一遍
- 每次都重新踩坑
- 每次只记得当前对话
- 做过的小改进无法形成复利

而自我进化真正想要的，不是“这次临场救火成功”，而是：

**这次补过的洞，下次默认就更稳。**

这就要求必须有一个专门的长期记忆层，来存放：
- 卡点历史
- fallback 历史
- 已跑通的工作流
- 成功补洞案例
- 失败教训
- 可升级为系统默认做法的候选资产

---

## 这层应该记什么

### 1. Bottleneck History
记录反复出现的卡点。

### 2. Fallback History
记录实际跑过的 fallback。

### 3. Improvement Assets
记录已经沉淀出的资产。

### 4. Reusable Patterns
记录跨任务、跨 skill 都能复用的方法模式。

### 5. Promotion Candidates
记录那些值得从“局部经验”升级成“系统默认做法”的候选项。

---

## 当前建议的目录结构

- `self-evolution/se-ltm-layer/README.md`
- `self-evolution/se-ltm-layer/bottleneck-history.md`
- `self-evolution/se-ltm-layer/fallback-history.md`
- `self-evolution/se-ltm-layer/improvement-assets.md`
- `self-evolution/se-ltm-layer/reusable-patterns.md`
- `self-evolution/se-ltm-layer/promotion-candidates.md`

---

## 和现有文件怎么分工

### `worklog.md`
记录当次事件。

### `se-ltm-layer/`
记录长期资产。

一句话：

**worklog 记当次事件，SE-LTM Layer 记长期资产。**
