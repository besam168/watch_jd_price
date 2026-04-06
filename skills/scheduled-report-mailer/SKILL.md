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
- `config/report-config.json`：任务、邮箱、白名单源、抓取策略配置
- `state/`：最近一次运行状态
- `logs/`：运行日志

## 默认抓取策略（至少 6 层）
1. **rss-feed**：主头条发现、发布时间过滤、0-24 小时硬窗口
2. **structured-market-data**：股市、黄金、布伦特、个股快照
3. **web-fetch**：单页正文补抓与快速验证
4. **desearch-crawl**：白名单站点清洗抓取
5. **ddg-discovery**：扩展今日候选新闻池
6. **desktop-verification**：只做页面验证，不做日报主采集

## 当前强规则
- 时间窗口：只取过去 0-24 小时
- 重点核查：加沙、乌克兰、中美经贸、美股、黄金、布伦特
- 重点源优先：Reuters / AP / BBC / Al Jazeera / NYSE / TWSE / SSE / JPX / KRX / CNBC / Yahoo Finance / Investing
- 每条核心新闻都要带来源和发布时间
- 抓不到就写“今日无重大更新”
- 严禁拿旧闻补洞，严禁虚构

## 注意
- 邮件发送走本机 SMTP 配置
- 定时任务默认写 Python 绝对路径，避免 Task Scheduler 找不到 `python`
- 数据采集应优先多来源 fallback，避免单点依赖
