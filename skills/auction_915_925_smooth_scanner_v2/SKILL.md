---
name: auction_915_925_smooth_scanner_v2
description: 基于 auction_915_925_smooth_scanner 的新版集合竞价狙击手插件。在 09:24:30 附近扫描沪深主板中小票，按“三安模式（稳健抬升型）”与“金螳螂模式（洗盘回落型）”两类逻辑输出候选股。默认复用 pytdx 快照与 8亿股+150亿主板基础池，适用于盘前 09:25 前快速狙击与竞价复盘。
---

# auction_915_925_smooth_scanner_v2

这是一个**集合竞价狙击手 V2** 插件，底盘继承自 `auction_915_925_smooth_scanner`，但目标不再只是“轨迹平滑”，而是直接按**策略分型**抓 09:24:30 的竞价机会。

## 核心模式

### 1. 稳健型（三安模式）
满足以下条件：
- 09:20 后价格重心平稳抬升
- 当前涨幅在 **+2% ~ +5%**
- 竞价量比 **> 1.5**

### 2. 洗盘型（金螳螂模式）
满足以下条件：
- 09:15~09:19 期间触及过接近涨停/冲板高位
- 09:20 后撤单回落至 **+1% ~ +5%**
- 09:24:30 时竞价量比 **> 2.5**

## 触发时间
- 默认目标触发点：**每个交易日 09:24:30**
- 输出要求：**09:25 前**生成列表结果

## 数据路线
- 默认主数据接口：**pytdx / 通达信协议**
- 默认股票池：**8亿股 + 150亿** 主板基础池
  - 文件：`outputs/liutong8yi_marketcap150yi_universe_full.json`
- 默认排除：创业板、科创板、北交所、ST/*ST、退市整理样式股票、上市未满60天新股/次新股

## 默认执行
```powershell
python {baseDir}/pipeline/run_v2.py --date auto_today
```

快速试跑：
```powershell
python {baseDir}/pipeline/run_v2.py --date auto_today --limit 300
```

## 标准输出
默认生成：
- `outputs/auction_sniper_v2_YYYYMMDD.csv`
- `outputs/auction_sniper_v2_YYYYMMDD.json`
- `outputs/auction_sniper_v2_YYYYMMDD.md`

## 输出字段
- `mode`：模式分类（sanan / jinmantang）
- `symbol`
- `name`
- `change_pct`
- `volume_ratio`
- `price_092430`
- `price_0915_ref`
- `price_0919_high`
- `price_0920_ref`
- `score`
- `passed`
- `fail_reasons`

## 输出原则
- 中文输出
- 明确模式分类
- 明确失败原因
- 若为快照近似或降级推断，必须在结果里标注说明
