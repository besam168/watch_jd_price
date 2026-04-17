# Worklog -> Radar 联动说明

> 用途：当真实工作里的卡点，已经不是只靠现场经验就能补完，而是需要借助外部世界找方法、找实现、找备用路线时，按这条联动流程执行。

---

## 什么时候触发这条联动

当 worklog 里某条记录出现以下情况时，就应该考虑启动 `self-evolution-radar`：
- 当前问题不是一次性小 bug，而是能力缺口
- 需要看外部世界有没有成熟做法、替代路线、候选 repo
- 需要借 Reddit 看真实用户痛点、争议点、趋势变化
- 需要借 GitHub 看真实实现、README、目录结构、维护痕迹
- 当前工作如果不补这层外部输入，下次还会重复踩坑

---

## 联动流程（默认顺序）

### 1. 先记 worklog
先把这次真实工作里的卡点写清楚：
- 工作场景
- 本次目标
- 卡点是什么
- 当场怎么先做完
- 根因判断
- 想补成什么能力资产

如果连卡点都没描述清楚，就不要急着巡逻。

### 2. 再对照 watchlist
看这次卡点更接近哪一类方向：
- `agent`
- `browser-automation`
- `memory`
- `openclaw`
- `general`

如果明确不了，就先用 `general`。

### 3. 再启动 radar
按主题跑一轮最小真实巡逻，例如：

```powershell
python .\skills\self-evolution-radar\scripts\run_real_patrol.py --topic agent --source both
```

或者：

```powershell
python .\skills\self-evolution-radar\scripts\run_real_patrol.py --topic browser-automation --source github
```

### 4. 先看 summary，不要先埋头翻原始结果
优先看：
- `patrol-summary-*.md`

因为这份摘要已经先做了：
- Reddit 热点整理
- GitHub 候选 repo 列举
- 值得深读的 3 个重点
- 可回灌方法
- 下一步建议动作

### 5. 再回写 worklog
把巡逻结论补回原来的 worklog 记录：
- 哪个方向值得追
- 哪个 repo 值得深读
- 哪个方法值得回灌
- 应沉淀成脚本 / skill / 模板 / 工作流里的哪一种

---

## 最小闭环标准

一条合格的 `worklog -> radar` 联动，至少要形成：
1. 一条真实工作卡点记录
2. 一轮与该卡点相关的外部巡逻
3. 一份结构化摘要
4. 一条回写后的沉淀动作结论

如果只有巡逻，没有回写到工作卡点，那这条联动就还没完成。

---

## 一句话记住

**worklog 负责记录“这次工作卡在哪”，radar 负责补“外部世界怎么做”，最后还要回到自己的脚本 / skill / 模板 / 工作流。**
