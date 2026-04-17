# self-evolution-radar

这是 `self-evolution` 项目的 skill 化版本。

## 当前包含内容

- `SKILL.md`：触发条件、工作流、输出口径、边界定义
- `scripts/run_real_patrol.py`：最小真实巡逻脚本
- `references/`：原项目中的方法文档、执行清单、教程与学习日志

## 当前状态

这是一个 **可复用的外部巡逻 skill 原型 V1 / V2 过渡版**。

它已经能承载：
- 研究雷达触发
- 方法参考
- 最小真实抓取
- 结构化输出口径
- Markdown 巡逻摘要生成

但它还不是成熟平台；当前仍以“人做判断 + 脚本拉素材”为主。

## 典型用途

- 巡逻 Reddit / GitHub 最近值得关注的新方向
- 做 AI agent / automation / memory / browser automation 学习雷达
- 找值得深读的候选 repo
- 给当前项目输出可回灌的方法建议
- 作为 `self-evolution` 中 `worklog -> radar -> 回写` 闭环的一部分，专门负责外部输入这一步

## 运行脚本

```powershell
python .\skills\self-evolution-radar\scripts\run_real_patrol.py
```

也支持参数化运行，例如：

```powershell
python .\skills\self-evolution-radar\scripts\run_real_patrol.py --topic agent --source both --reddit-limit 5 --github-limit 10
python .\skills\self-evolution-radar\scripts\run_real_patrol.py --topic memory --source github --github-limit 15
python .\skills\self-evolution-radar\scripts\run_real_patrol.py --topic openclaw --output .\skills\self-evolution-radar\patrol-openclaw.txt
```

当前支持的核心参数：
- `--topic`
- `--source`
- `--reddit-limit`
- `--github-limit`
- `--output`
- `--summary-output`
- `--no-summary`

内置 topic preset：
- `general`
- `agent`
- `browser-automation`
- `memory`
- `openclaw`

运行后会在脚本设定的输出位置生成巡逻结果文本。
默认还会再生成一份 Markdown 巡逻摘要，方便直接做人工筛选和后续回灌。

## 后续建议

下一阶段建议继续补：
- topic / watchlist 外置配置
- 输出目录规范
- 轻量评分
- 历史归档
- 周报模板
- 调度入口

同时建议把它默认放在这条链路里使用：

`worklog -> watchlist/topic 判断 -> self-evolution-radar -> summary -> 回写 worklog`
