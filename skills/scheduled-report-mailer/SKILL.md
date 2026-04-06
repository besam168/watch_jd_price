---
name: scheduled-report-mailer
description: 定时收集新闻和市场数据、生成中文报告并发送邮件的技能。适用于需要把“采集 -> 写报告 -> 发邮件 -> 安装计划任务”收成一个可维护插件时使用。支持早报/晚报调度、状态文件、日志，以及多数据源 fallback，不依赖单一 Firecrawl。
---

# Scheduled Report Mailer

用于把“定时收集内容、写报告、发 email”收成一条统一链路。

## 何时使用
- 用户要新建一个独立插件来跑定时报告
- 用户要统一“采集 / 写报告 / 发邮件 / 定时任务”
- 现有脚本分散，想收敛成可维护目录

## 默认工作流
1. 编辑 `config/report-config.json`
2. 运行 `scripts/run-job.py --job <job-name> --collect-only` 验证采集
3. 运行 `scripts/run-job.py --job <job-name>` 验证完整收集+发信
4. 运行 `scripts/install-tasks.ps1` 安装/更新计划任务
5. 检查 `logs/` 与 `state/last-*.json`

## 目录约定
- `scripts/run-job.py`：单次执行入口
- `scripts/install-tasks.ps1`：安装 Windows 计划任务
- `config/report-config.json`：任务与邮箱配置
- `state/`：最近一次运行状态
- `logs/`：运行日志

## 注意
- 邮件发送走本机 SMTP 配置
- 定时任务默认写 Python 绝对路径，避免 Task Scheduler 找不到 `python`
- 数据采集应优先多来源 fallback，避免单点依赖
