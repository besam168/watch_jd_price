---
name: a-share-live-smallcap
description: 盘中筛选A股“正在动的中小盘强势股”。适用于用户想在早盘或盘中，从实时强势热股里先剔除大票/权重，再保留中小盘、创业板、次新、科创与高弹性方向，最后叠加“近3日放量拉升 + 5日线宽松辅助”过滤时使用。不替代 a-share-opening-flow-v6-test，而是独立补充一个更偏中小盘实战的版本。
---

# A股盘中中小盘强势股插件

## 定位
这个插件是 **a-share-opening-flow-v6-test 的独立补充版**。

它不改原插件逻辑，专门解决一个问题：

**原 V6 测试版容易先抓到大票/权重；这个版本优先抓盘中正在动的中小盘强势股。**

一句话：

**实时强势热股 → 剔除大票/权重 → 保留中小盘/创业板/次新/弹性票 → 再套 V6 的近3日量价 + 5日线过滤。**

## 适用场景
当用户表达以下意图时用它：
- 盘中选股，但不想全是权重大票
- 想看中小盘、创业板、次新、科创弹性票
- 想找“盘中正在动”的强势股，而不是只看固定候选池
- 想保留 V6 测试版的 3 日量价共振过滤思路

## 输出重点
建议重点看这几类：
- **true_leaders**：盘中最像真龙头的中小盘强势股
- **strong_followers**：强跟风/强跟随票
- **pseudo_strong**：伪强票，盘中看着强但过滤不完整
- **watchlist**：适合盯盘的前排名单
- **chinese_summary**：一段可直接拿去盯盘的中文结论
- **rejected_largecap**：被剔除的大票/权重
- **rejected_live**：实时强度或风格不过关的票

## 建议脚本
```powershell
python {baseDir}/scripts/live_smallcap.py --json
```

## 常用参数
```powershell
python {baseDir}/scripts/live_smallcap.py --json
python {baseDir}/scripts/live_smallcap.py --top-n 120 --pick-count 24 --json
python {baseDir}/scripts/live_smallcap.py --min-change-pct 1.5 --min-amount-yi 2 --json
python {baseDir}/scripts/live_smallcap.py --min-turnover-ratio 5 --json
python {baseDir}/scripts/live_smallcap.py --max-total-mv-yi 1200 --max-circ-mv-yi 800 --json
python {baseDir}/scripts/live_smallcap.py --allow-mainboard-60 --json
```

## 默认原则
- **停用旧实时入口**：东方财富实时全市场、新浪全市场涨幅榜不再进入主流程
- **统一改用 `pytdx.hq.TdxHq_API`** 快照扫描
- 复用 `auction_915_925_smooth_scanner` 已跑通的数据层：
  - 多服务器 fallback
  - 批量快照拉取
  - 单批失败降级补拉
  - 统一字段输出格式
- 股票池直接复用 **`5亿股 + 100亿流通市值`** 新股票池
- 盘中版本已升级为 **多轮采样**：默认不再只看单帧快照，而是短窗口连续采样后再评分
- 最后仍以 V6 测试版的日线过滤作收口

## 推荐执行入口
- 主扫描：`python {baseDir}/scripts/live_smallcap.py --json`
- 双时点任务：
  - `python {baseDir}/scripts/scheduled_smallcap_dual_phase.py 0935`
  - `python {baseDir}/scripts/scheduled_smallcap_dual_phase.py 0945`

## 双时点分工
- **09:35 = 先手苗子池**
  - 偏放宽
  - 重点抓早盘刚冒头、刚放量、刚有轨迹的小票
  - 更适合做“先看谁冒出来”
- **09:45 = 留强确认池**
  - 偏确认
  - 重点保留已经走出来、强度还在延续、没有明显掉队的票
  - 更适合做“谁值得继续盯”

## 注意
- 当前版本已按要求**停掉东财 / 新浪旧主流程入口**，不再用于实时候选获取。
- 定时脚本 `scheduled_smallcap_scan.py` / `scheduled_smallcap_final.py` 也已切到 **pytdx + 5亿股/100亿新池**，不再走旧口。
- 新增了 **双时点多轮采样版**，适合 09:35 / 09:45 两个时点做更像盘中实战的扫描。
- 若 pytdx 节点抽风，主流程会在 pytdx 多节点之间 fallback，不再退回东财/新浪。
- 若用户明确说“不要改原版”，就继续保留原 `a-share-opening-flow-v6-test` 不动，只单独调用这个插件。
