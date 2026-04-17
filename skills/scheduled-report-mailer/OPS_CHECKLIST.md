# OPS_CHECKLIST（scheduled-report-mailer 运维检查清单）

> 目标：让值班同学 30 秒看清“先抓什么、失败怎么回退、去哪看证据”。

## 0) 一眼总览（执行顺序）

按策略优先级固定为：
1. `rss-feed`
2. `structured-market-data`
3. `web-fetch`
4. `desearch-crawl`
5. `ddg-discovery`
6. `desktop-verification`

配置来源：`config/report-config.json` -> `collection_policy.capture_strategies`

---

## 1) 宏观新闻模块（头条 + 地缘）

### 1.1 先抓顺序

**头条主链：**
1. QVeris 新闻接口（可用则优先）
2. RSS（固定顺序）
   - BBC World
   - AP News
   - CNBC World
3. 多搜索发现（发现补充）
   - 搜索引擎顺序：DuckDuckGo -> Startpage -> Yahoo
   - 站点顺序：Reuters -> BBC -> AP -> Al Jazeera -> CNBC -> Guardian -> The Verge -> TechCrunch
4. 正文证据校验（无正文证据不进入核心头条）

**地缘专题链：**
- BBC -> Reuters 主站 -> Reuters Europe -> Reuters China -> AP -> Al Jazeera

### 1.2 失败回退

- 头条不足：
  - 允许发现候选，但**无正文证据不入稿**
  - 触发 `headline_evidence_gate` 检查
- 地缘分区抓不到：
  - 直接写“今日无重大更新”
  - 禁止旧闻补洞

### 1.3 运维检查点

- 看 `reports/scheduled/latest_report_evidence.json`
  - `headlineCount`
  - `headlineEvidenceCount`
  - `hasPlaceholderSearchDiscovery`
- 看 `state/report-evaluation.json`
  - `headlineEvidenceGate.ok` 是否为 `true`
- 判断“内容命中”时，不要只死卡固定 `must-check` 词：
  - 只要属于**国际时事新闻**、来源与时间可信，也应先视为有效候选；
  - 再继续判断它有没有足够正文证据进入核心头条。

---

## 2) 市场与商品模块

### 2.1 先抓顺序（指数/股市）

1. 页面抓取解析（本地 `.firecrawl`）：
   - Reuters / Yahoo / TWSE / JPX / KRX / Eastmoney
2. 新浪实时接口覆盖（CN/HK/US 代理）
3. QVeris 快照补充/覆盖（AAPL/NVDA/TSLA + 指数代理）

### 2.2 先抓顺序（商品）

1. Yahoo 商品页：GC=F / BZ=F / CL=F
2. QVeris 商品：XAUUSD / BZUSD / CLUSD

### 2.3 失败回退

- 单项抓不到：写“今日无重大更新”
- 只抓到区间：可写“仅抓到区间”，不补历史数字
- 明显异常值：拦截，不入稿

### 2.4 运维检查点

- 看 `reports/scheduled/latest_collect_status.json`：
  - `market_snapshot_refresh` 是否 `ok=true`
- 看 `reports/scheduled/qveris_market_snapshot.json` 是否有新内容
- 看最终报告市场段是否还存在旧数字补洞迹象（应无）

---

## 3) 科技新闻模块

### 3.1 先抓顺序（固定）

1. The Verge
2. TechCrunch
3. IEEE Spectrum
4. Wired
5. Ars Technica
6. MIT Technology Review
7. VentureBeat AI
8. Singularity Hub
9. AI News
10. Engadget

### 3.2 失败回退

- 无可用内容：输出“今日无重大更新”
- 最终仍受科技白名单过滤（非白名单来源不入稿）

### 3.3 运维检查点

- 报告“科技板块”是否出现来源越界
- “科技板块”是否挤占宏观头条（若挤占，回看头条优先级与证据门）

---

## 4) 桌面 fallback（兜底，不是主链）

### 4.1 触发条件（conditional_trigger）

满足任一可触发：
- 质量门非 pass
- 头条数不足
- 证据数不足
- 出现占位搜索发现
- 报告中出现“今日无额外摘要”标记

### 4.2 执行动作

- 打开目标 URL（默认 BBC）
- 截图首屏 + 轻微下拉后截图
- 两次 OCR
- 标题匹配校验
- 结果写入状态文件

### 4.3 运维检查点

- `state/desktop-fallback-status.json`
- `logs/comprehensive-morning.log` 中：
  - `DESKTOP_FALLBACK_DECISION`
  - `DESKTOP_FALLBACK`
  - `EVALUATE_AFTER_FALLBACK`

---

## 5) 日常巡检（最短路径）

1. 跑采集（不发信）
```bash
python skills/scheduled-report-mailer/scripts/run-job.py --job comprehensive-morning --collect-only
```
2. 看主状态：`state/last-comprehensive-morning.json`
3. 看采集状态：`reports/scheduled/latest_collect_status.json`
4. 看验收：`state/report-evaluation.json`
5. 看成品：`reports/scheduled/latest_report.txt`

通过标准：
- `status=pass`
- 头条有来源+时间
- 市场/商品无旧值补洞
- 抓不到处明确写“今日无重大更新”

---

## 6) 快速处置指引

- **问题：头条太少**
  - 先看 `headlineEvidenceCount`，再看多搜索发现是否拿到正文证据
  - 不要把“没命中固定关键词”直接等同于“没有有效内容”；先判断是否已有可信国际时事候选
- **问题：市场数据陈旧**
  - 先看 `market_snapshot_refresh`，再看 QVeris 快照是否更新
- **问题：内容质量一般/模板感重**
  - 优先修头条发现与正文证据链，不先动发送策略
  - 默认区分两层：
    1. 是否已有可信国际时事候选；
    2. 这些候选是否拿到了足够正文证据进入核心头条

---

## 7) 变更纪律

- 先改小、再验证
- 任何回退文案保持诚实：抓不到就写“今日无重大更新”
- 不伪造、不补旧闻
- 涉及 `delivery_policy.send_on_partial` 的变更，默认按以下顺序执行：
  1. 先确认 `config/report-config.json` 当前真实值；
  2. 再看最近一次 `logs/*.log` 中 `SUMMARY` / `SEND` 的实际行为；
  3. 再同步更新 README / OPS 文档；
  4. 最后保留一轮最小真测日志，避免“文档已改但运行事实未验证”。
