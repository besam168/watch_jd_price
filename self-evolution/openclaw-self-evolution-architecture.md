# OpenClaw 自我进化架构蓝图

> 用途：定义 `self-evolution` 如何从当前的“单闭环原型”，逐步演进成可作用于整个 OpenClaw 系统的一层方法架构。

---

## 1. 这份蓝图要解决什么问题

当前 `self-evolution` 已经能在一个局部闭环里跑通：
- 真实工作里发现卡点
- 记录到 worklog
- 必要时启动 radar
- 形成 summary
- 回写结论
- 沉淀出 SOP / fallback / skill / 脚本

这已经是一个可工作的原型。

但如果目标只是把它留在 `self-evolution-radar` 这一个 skill 里，那天花板会很低。

大目标应该是：

**把“发现卡点 -> 补能力缺口 -> 沉淀资产 -> 全局复用”做成一层可推广到整个 OpenClaw 系统的方法架构。**

---

## 2. 三层演进路线

### 第一层：单闭环验证层（现在）
作用：
- 先在一个局部场景把方法跑通
- 先验证 worklog、fallback、radar、回写是否真有用
- 先积累最小真实样板

当前典型载体：
- `self-evolution/worklog.md`
- `self-evolution/bottleneck-template.md`
- `self-evolution/worklog-radar-loop.md`
- `self-evolution/fallback-search-and-crawl-workflow.md`
- `skills/self-evolution-radar`

目标不是做大，而是做实。

---

### 第二层：多 skill 复用层（下一阶段）
作用：
- 让不止一个 skill 接入这套方法
- 让“局部改进”开始可迁移
- 让多个 skill 共享问题分类、fallback 思路、沉淀方式

这一层可能出现的东西：
- 统一 bottleneck 分类法
- 统一 fallback playbook 模板
- 统一 worklog / improvement log 结构
- skill 级问题回写机制
- 不同 skill 共用的改进 checklist

典型适用对象：
- 搜索 / 抓取 skill
- 网页抓取 / scrape skill
- 报告生成 skill
- 桌面自动化 / browser automation skill
- 未来的新技能模块

---

### 第三层：OpenClaw 系统方法层（理想形态）
作用：
- 让“自我进化”不再依赖某个具体 skill
- 让整个 OpenClaw 系统具备更强的稳定性与可复用演进能力
- 让某次补洞能逐步升级成系统默认做法

理想状态下，它可能表现为：
- 统一的 bottleneck intake 入口
- 统一的 fallback 策略层
- 统一的系统改进资产目录
- 从 skill 级成功经验提升为系统级默认策略的机制
- 更明确的“局部问题 -> 系统优化”升级路径

注意：这仍然是方向蓝图，不代表现在已经做完。

---

## 3. 哪些是“方法层”，哪些是“具体 skill”

### 方法层（应该尽量可迁移）
这些东西不应绑定死某一个 skill：
- `worklog` 思想
- bottleneck 模板
- fallback 顺序设计
- radar 触发条件
- 回写机制
- 资产沉淀原则
- 从局部问题升级成系统默认做法的判断标准

这些属于：

**self-evolution 的方法层。**

---

### 具体 skill（属于局部执行层）
这些东西可以随具体 skill 不同而不同：
- 某个 skill 的抓取脚本
- 某个 skill 的 topic 预设
- 某个 skill 的输出结构
- 某个 skill 的数据源
- 某个 skill 的局部 fallback 路线

比如：
- `self-evolution-radar`
- 未来的搜索 fallback skill
- 未来的网页抓取 fallback skill
- 某个报告类 skill 的自我改进闭环

这些属于：

**self-evolution 的执行层 / skill 层。**

---

## 4. 系统级最关键的 5 个接口

如果以后真要把这套东西推广到整个 OpenClaw，最值得先抽象的不是“所有功能”，而是下面 5 个接口。

### 接口 1：Bottleneck Intake
解决：
- 问题从哪里进入系统
- 什么才算值得记录的卡点

当前原型：
- `worklog.md`
- `bottleneck-template.md`

未来方向：
- 统一的系统级卡点入口

---

### 接口 2：Fallback Playbook
解决：
- 遇到不稳定路线时，默认先怎么切换
- 哪些 fallback 属于局部经验，哪些应升级为默认 SOP

当前原型：
- `fallback-search-and-crawl-workflow.md`

未来方向：
- 分类明确的 fallback 路线库

---

### 接口 3：External Learning / Radar
解决：
- 什么时候要借外部世界找方法
- 什么时候不需要巡逻，直接补洞就够

当前原型：
- `self-evolution-radar`
- `worklog-radar-loop.md`

未来方向：
- 针对不同能力带的专门 radar 模块

---

### 接口 4：Write-back / Improvement Record
解决：
- 巡逻完、补洞完，结果落到哪里
- 哪些改进只是一次性，哪些值得长期保留

当前原型：
- `worklog.md`
- `memory/2026-04-17.md`
- `self-evolution/se-ltm-layer/`

未来方向：
- 更稳定的改进资产目录和记录标准
- 长期可检索、可复用、可升级的**自我进化长期记忆层**（Self-Evolution Long-Term Memory Layer, SE-LTM Layer）

---

### 接口 5：Promotion to System Default
解决：
- 某个 skill 跑通的做法，什么时候可以升级为整个系统默认做法
- 如何避免“局部经验”误当“全局标准”

当前还没做成，只是蓝图方向。

---

## 5. 当前阶段最现实的推进策略

### 不应该做的
- 不要现在就吹成“整个 OpenClaw 已有自我进化系统”
- 不要跳过局部验证，直接设计大而空的平台
- 不要把所有 skill 一次性接入，结果全都半成品

### 应该做的
1. 先继续把单闭环做实
2. 从单闭环里抽出可复用的方法层
3. 选择第二个、第三个 skill 做小范围复用测试
4. 只有当复用稳定后，才考虑系统级默认接口

一句话：

**先局部跑通，再抽象共性，再推广系统。**

---

## 6. 当前与未来的边界

### 现在可以说
- 已经有单闭环原型
- 已经能跑真实样板
- 已经开始形成 SOP 与 fallback 文档
- 已经具备向多 skill 复用演进的方向
- 已经开始搭建**自我进化长期记忆层**（SE-LTM Layer）雏形

### 现在不能说
- 不能说整个 OpenClaw 已完成自我进化系统接入
- 不能说已经具备系统级统一接口
- 不能说所有 skill 都能自动发现并修补问题

---

## 7. 下一步最值得做什么

基于这份蓝图，后续最值钱的动作不是继续抽象，而是：

### 近端
- 再选 1~2 个 skill 做复用验证
- 补一份 `fallback-routes.md`
- 补更细的 bottleneck 分类

### 中程
- 把 worklog / fallback / radar 进一步整理成可共享模板
- 定义“什么样的局部经验可以升级成系统默认做法”

### 长程
- 考虑是否做系统级的 bottleneck intake / improvement registry

---

## 一句话总结

**`self-evolution` 当前先是一个闭环原型；下一步要变成多 skill 可复用的方法层；更长远的理想，是成为整个 OpenClaw 系统的一层自我进化架构。**
