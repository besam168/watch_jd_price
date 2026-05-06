---
name: shakeout-dragon-capture
description: 基于 auction_915_925_smooth_scanner_v2 股票池与 pytdx 行情底座的短线强势股“异动倍量·洗盘擒龙战法”插件。筛选近6日强势连阳、倍量异动阳线、3日缩量洗盘且不破异动日开盘价的候选股，用于捕捉空中加油后二次爆发机会。
---

# Shakeout Dragon Capture

英文名：`Shakeout Dragon Capture`

中文战法名：**异动倍量·洗盘擒龙战法**

## 核心逻辑

1. 过去 6 个交易日内阳线数 `>= 4`
2. 信号日默认扫描 `T-2 / T-3 / T-4`
3. 信号日必须满足：
   - 倍量：`V(signal) >= 2 * V(prev)`
   - 阳线：`C(signal) > O(signal)`
4. 后续 3 日必须满足：
   - `Low >= O(signal)`
   - `V < V(signal)`
   - 平均量能 `< 0.7 * V(signal)`
5. 可选增强：要求信号日触板/炸板

## 数据底座

- 股票池：复用 `auction_915_925_smooth_scanner_v2` 主板基础池
- 实时快照：复用 `pytdx_snapshot.py`
- 历史日线：使用 `pytdx get_security_bars(9, ...)`

## 主入口

```powershell
python {baseDir}/pipeline/run_all_in_one.py --limit 100
```

## 本地验收

```powershell
python {baseDir}/pipeline/validate_local.py
```

## 产物

- `outputs/shakeout_dragon_capture.json`
- `outputs/shakeout_dragon_capture.csv`
- `outputs/shakeout_dragon_capture.md`
