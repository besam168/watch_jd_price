---
name: auction_915_925_smooth_scanner_v2
description: 基于 auction_915_925_smooth_scanner 底盘改造的新版集合竞价狙击手插件。09:24:30 附近仅按“三安模式（稳健抬升型）”与“金螳螂模式（冲板回落型）”两套规则筛股，不再沿用旧版平滑扫描选股条件。默认复用 pytdx 快照与 8亿股+150亿主板基础池，适用于 09:25 前快速输出竞价狙击名单。
---

# auction_915_925_smooth_scanner_v2

这是一个**集合竞价狙击手 V2** 插件。

它虽然继承自 `auction_915_925_smooth_scanner` 的数据底盘，但**选股逻辑已经切换**：

- **删除旧版“轨迹平滑 / smooth_score / range_ratio / rmse_ratio”那套选股条件**
- **只保留新版两种模式规则**

## 唯一保留的选股条件

### 1. 三安模式（稳健型）
满足以下条件：
- 09:20 后价格重心平稳抬升
- 当前涨幅在 **+2% ~ +5%**
- 竞价量比 **> 1.5**

### 2. 金螳螂模式（洗盘型）
满足以下条件：
- 09:15~09:19 期间触及过涨停
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

连续轨迹采样（V2 真实轨迹基础版）：
```powershell
python {baseDir}/pipeline/capture_track_v2.py 300 6 5
```
说明：
- 第1个参数：扫描股票数上限
- 第2个参数：采样轮数
- 第3个参数：轮间隔秒数
- 当前会生成 `auction_sniper_v2_track_auto_today.json` 作为 09:15~09:24 连续轨迹基础数据


## 标准输出
默认生成：
- `outputs/auction_sniper_v2_YYYYMMDD.csv`
- `outputs/auction_sniper_v2_YYYYMMDD.json`
- `outputs/auction_sniper_v2_YYYYMMDD.md`

## 主输出格式
每条候选默认按以下格式表达：
- `[模式分类] 股票代码 - 名称 - 当前涨幅 - 竞价量比`

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
- `passed`
- `fail_reasons`

## 输出原则
- 中文输出
- 明确模式分类
- 明确失败原因
- 若为快照近似或降级推断，必须在结果里标注说明

## V2 当前进度说明
当前 V2 已分成两层：
1. **run_v2.py**：09:24:30 附近快照版规则筛选
2. **capture_track_v2.py**：09:15~09:24 连续采样轨迹捕获底座

也就是说，这版已经不只是单快照骨架，已经开始补“真实连续竞价轨迹”能力；后续可继续把三安模式/金螳螂模式从快照近似升级为连续轨迹精确判定。