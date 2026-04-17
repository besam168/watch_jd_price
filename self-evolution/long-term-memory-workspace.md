# Self-Evolution 长期记忆工作区

> 用途：为 `self-evolution` 提供一个**长期可积累、可检索、可回看、可升级** 的记忆工作区。这里不是单次对话缓存，而是自我进化过程的长期资产层。

---

## 为什么一定要有长期记忆工作区

如果没有长期记忆工作区，`self-evolution` 很容易退化成：
- 每次都重新想一遍
- 每次都重新踩坑
- 每次只记得当前对话
- 做过的小改进无法形成复利

而自我进化真正想要的，不是“这次临场救火成功”，而是：

**这次补过的洞，下次默认就更稳。**

这就要求必须有一个专门的长期记忆工作区，来存放：
- 卡点历史
- fallback 历史
- 已跑通的工作流
- 成功补洞案例
- 失败教训
- 可升级为系统默认做法的候选资产

---

## 这块工作区应该记什么

### 1. Bottleneck History
记录反复出现的卡点：
- 什么类型问题出现过
- 出现频率如何
- 哪些问题已经有 fallback
- 哪些问题还没有稳定解法

### 2. Fallback History
记录实际跑过的 fallback：
- 哪条路线有效
- 哪条路线只是临时顶一下
- 哪条路线值得升级为默认 SOP

### 3. Improvement Assets
记录已经沉淀出的资产：
- 脚本
- skill
- 模板
- SOP
- 执行顺序
- 参考文档

### 4. Reusable Patterns
记录跨任务、跨 skill 都能复用的方法模式：
- 哪种补洞顺序最稳
- 哪种输出结构最适合回写
- 哪类任务适合先 local 再 external
- 哪类问题适合优先走 radar

### 5. Promotion Candidates
记录那些值得从“局部经验”升级成“系统默认做法”的候选项。

---

## 当前建议的目录结构

建议把长期记忆工作区单独放在：

- `self-evolution/memory-workspace/`

当前先建议最小结构：

- `self-evolution/memory-workspace/README.md`
- `self-evolution/memory-workspace/bottleneck-history.md`
- `self-evolution/memory-workspace/fallback-history.md`
- `self-evolution/memory-workspace/improvement-assets.md`
- `self-evolution/memory-workspace/reusable-patterns.md`
- `self-evolution/memory-workspace/promotion-candidates.md`

---

## 这块工作区和现有文件怎么分工

### `worklog.md`
记录：
- 当次工作里发生了什么
- 这次卡点是什么
- 这次怎么先处理的

它更像“事件入口”。

### `memory-workspace/`
记录：
- 长期反复有价值的经验
- 已经证明有效的 fallback
- 值得复用的模式
- 值得升级成系统默认做法的候选项

它更像“长期资产层”。

一句话：

**worklog 记当次事件，memory-workspace 记长期资产。**

---

## 当前阶段怎么用

现阶段不需要一下子把它做成复杂数据库。

先按文档型工作区来用就够了：
1. 真实工作里出现卡点，先记 `worklog`
2. 如果某条经验已经重复出现或证明有效，就提炼进 `memory-workspace`
3. 如果某项经验已经明显具有跨 skill 价值，就放进 `promotion-candidates.md`
4. 后续做多 skill 复用时，优先从这块长期记忆工作区取素材

---

## 一句话总结

**`self-evolution` 不只需要 worklog，还必须有一块长期记忆工作区；否则它只能算会记录问题，不能算真正会积累能力。**
