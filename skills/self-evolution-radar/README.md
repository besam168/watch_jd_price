# self-evolution-radar

这是 `self-evolution` 项目的 skill 化版本。

## 当前包含内容

- `SKILL.md`：触发条件、工作流、输出口径、边界定义
- `scripts/run_real_patrol.py`：最小真实巡逻脚本
- `references/`：原项目中的方法文档、执行清单、教程与学习日志

## 当前状态

这是一个 **可复用的外部巡逻 skill 原型 V1**。

它已经能承载：
- 研究雷达触发
- 方法参考
- 最小真实抓取
- 结构化输出口径

但它还不是成熟平台；当前仍以“人做判断 + 脚本拉素材”为主。

## 典型用途

- 巡逻 Reddit / GitHub 最近值得关注的新方向
- 做 AI agent / automation / memory / browser automation 学习雷达
- 找值得深读的候选 repo
- 给当前项目输出可回灌的方法建议

## 运行脚本

```powershell
python .\skills\self-evolution-radar\scripts\run_real_patrol.py
```

运行后会在脚本设定的输出位置生成巡逻结果文本。

## 后续建议

下一阶段建议继续补：
- 参数化配置
- 输出目录规范
- 自动摘要
- 历史归档
- 周报模板
- 调度入口
