---
name: a-share-live-smallcap
description: 盘中筛选A股“正在动的中小盘强势股”。适用于用户想在早盘或盘中，从实时强势热股里先剔除大票/权重，再保留中小盘、创业板、次新、科创与高弹性方向，最后叠加“近3日放量拉升 + 5日线宽松辅助”过滤时使用。不替代 a-share-opening-flow-v6-test，而是独立补充一个更偏中小盘实战的版本。
---

# A股盘中中小盘强势股插件 V2

## 定位
这个插件是 **a-share-opening-flow-v6-test 的独立补充版 V2**。

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
python {baseDir}/scripts/live_smallcap.py --max-total-mv-yi 1200 --max-circ-mv-yi 800 --json
python {baseDir}/scripts/live_smallcap.py --allow-mainboard-60 --json
```

## 默认原则
- 优先抓实时涨幅靠前、成交额不太差的票
- 先排除明显大票/权重
- 创业板、次新、科创、中小盘主板给更高优先级
- 最后仍以 V6 测试版的日线过滤作收口

## 注意
- 这个版本更偏 **实战盘中扫描**，不是静态白名单版本。
- 实时接口如果抽风，会自动 fallback 到较小候选池，但结果会更保守。
- 若用户明确说“不要改原版”，就继续保留原 `a-share-opening-flow-v6-test` 不动，只单独调用这个插件。
