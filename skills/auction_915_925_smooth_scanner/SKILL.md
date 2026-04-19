---
name: auction_915_925_smooth_scanner
description: 扫描沪深主板中小票在 09:15-09:25 集合竞价阶段，寻找价格分时轨迹平滑、接近直线且具备基本成交参与度的股票。仅使用竞价时段数据，排除创业板、科创板、北交所和上市未满60个交易日的新股/次新股，输出候选列表、指标拆解、评分、失败原因与数据源来源。适用于集合竞价纯筛选、盘前风向确认、竞价轨迹复核。
---

# auction_915_925_smooth_scanner

这是一个**纯 9:15–9:25 集合竞价版** A 股扫描插件。

## 股票池范围
默认只扫描：
- **沪深主板里的中小票**
- 优先使用 **深市 00 开头主板票** 作为核心池

默认排除：
- **创业板**（如 `300xxx` / `301xxx`）
- **科创板**（如 `688xxx` / `689xxx`）
- **北交所**（如 `8xxxxx` / `4xxxxx`）
- **上市未满 60 个交易日的新股/次新股**
- ETF、基金、可转债等非普通股票品种

## 硬约束
- 只使用 **09:15:00 ~ 09:25:00** 数据
- 禁止使用 **09:30 之后** 的任何数据
- 禁止用日K或普通盘中K线冒充竞价逐点数据
- 如数据源只能提供分钟聚合，必须标记为 `minute_agg` 降级

## 目标
从沪深主板中小票中找出：
- 竞价轨迹波动小
- 相邻跳点离散低
- 价格变化次数少
- 线性拟合残差小
- 具备基本成交参与度

## 默认执行
```powershell
python {baseDir}/pipeline/run.py --date auto_today
```

指定日期：
```powershell
python {baseDir}/pipeline/run.py --date 2026-04-20
```

仅扫描自定义股票：
```powershell
python {baseDir}/pipeline/run.py --date 2026-04-20 --universe-mode custom --symbols sh600703 sz000001
```

## 标准输出
默认生成：
- `outputs/auction_smooth_YYYYMMDD.csv`
- `outputs/auction_smooth_YYYYMMDD.json`
- `outputs/auction_smooth_YYYYMMDD.md`

## 核心指标
- `range_ratio`
- `jump_std_ratio`
- `change_ratio`
- `rmse_ratio`
- `amt_float_ratio`

## 数据源优先级
1. 腾讯（主）
2. 东方财富（备）
3. 新浪（兜底）

所有数据源都必须归一到统一 `auction_ticks` 结构，再进入指标计算。

## 输出原则
- 中文输出
- 明确标记数据源
- 明确标记失败原因
- 如为降级数据，必须写明粒度与置信度下降
