# a-share-opening-flow-v6-test

A股开盘风向与实时盯盘插件 V6 测试版。

## 作用
用于测试和校验筛选逻辑，重点验证：
- 候选池是否合理
- 过滤条件是否有效
- 共振核心是否与盘面匹配

这是测试 / 校验版本，不是当前主用正式版本。

## 入口
```bash
python scripts/opening_flow_v6_test.py --json
python scripts/opening_flow_v6_test.py
```

## 当前状态
已做稳定性修复，但仍然定义为测试版。
适合：
- 对照正式版结果
- 测过滤逻辑
- 做回归检查

## 当前稳定数据源策略
- 东方财富：默认禁用
- 新浪 / 腾讯：盘中实时主源
- 腾讯历史K线（akshare）：日线过滤
- 板块热度：新浪 / 腾讯候选池分组 fallback

## 输出内容
- `top_sectors`
- `first_round_candidates`
- `passed`
- `partial`
- `failed`
- `resonance_core`
- `resonance_follow`
- `data_sources`

## 与正式版的区别
- 这是实验 / 校验口径
- 可用于验证正式版结果是否偏差过大
- 不建议单独作为唯一生产输出来源

## 常见故障
### 1. 候选池为空
优先排查实时源是否可用，而不是先怀疑过滤逻辑。

### 2. 板块为空
先看候选池是否为空；板块层本质依赖候选池。

### 3. 结果与正式版不同
这是正常现象，因为测试版更偏验证逻辑，不要求和正式版口径完全一致。

## 使用建议
- 正式盘中分析：优先正式版
- 交叉验证：使用本测试版
- 自动链兜底：允许本测试版作为 fallback