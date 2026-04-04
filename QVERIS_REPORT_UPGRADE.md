# QVeris 综合情报报告升级说明

## 本次升级目标

把 `daily_comprehensive_report.py` 从“仅 RSS / 本地快照兜底”升级为：

- **优先尝试 QVeris 新闻搜索增强**
- **QVeris 失败时自动回退到原 RSS 逻辑**
- 不让单一外部服务拖死每日定时任务

## 本次新增文件

- `qveris_report_helpers.py`

作用：
- 统一封装 QVeris 相关新闻搜索与行情查询入口
- 当前已接入：
  - `newsdata.news.search.v1.b65ccc56`
  - `finnhub_io_api.stock.quote`
  - `financialmodelingprep.stable.quote.retrieve.v1.822497ca`

## 当前主脚本改动

`daily_comprehensive_report.py` 已增加：
- 尝试导入 `qveris_report_helpers.fetch_news_items`
- 在 `fetch_rss_items()` 中优先使用 QVeris 新闻结果
- 若 QVeris 不可用、报错、超时，则自动回退到旧的 RSS 抓取逻辑

## 设计原则

1. **增强而不替代**
   - 不把原有稳定链路删掉
   - 先让 QVeris 做增强层，而不是单点依赖

2. **定时任务优先稳定**
   - 每天的报告宁可退回旧逻辑，也不能因 QVeris 瞬时异常而整轮失败

3. **便于后续继续扩展**
   - 后续可继续把美股、商品、科技新闻分模块接入 QVeris
   - 但必须继续保留 fallback

## 下一步建议

### P1
把市场报价也分阶段接入 QVeris：
- 美股指数相关代理数据
- 黄金/原油 quote
- A 股 / 港股可用工具补强

### P2
给新闻结果增加：
- 去重
- 来源优先级
- 中东 / 俄乌 / 中美 / AI / 桌面技术 分类

### P3
单独增加“桌面技术 / AI Agent / 自动化工具”增强板块

## 使用建议

日常定时任务无需改命令，仍保持：

```bash
python daily_comprehensive_report.py
```

当前脚本内部会自动：
1. 先试 QVeris
2. 失败则退回 RSS / 本地快照

这意味着现有计划任务可以直接沿用。
