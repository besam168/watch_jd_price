# a-share-opening-flow-v6-auto

A股开盘风向与实时盯盘插件 V6 自动指令版。

## 作用
按固定时间点自动输出盘中提示语，当前时间点为：
- 09:25
- 09:33
- 09:38
- 09:43
- 09:45

适合：
- 早盘自动盯盘
- 固定时间点播报
- 主线/强弱/上午主看名单自动生成

## 当前策略
- 正式版优先
- 测试版兜底

也就是：
1. 先调用 `a-share-opening-flow`
2. 若正式版失败或无有效输出，再调用 `a-share-opening-flow-v6-test`

## 入口
```bash
python scripts/opening_flow_v6_auto.py --dry-run
python scripts/opening_flow_v6_auto.py
```

## dry-run 用途
- 不等真实时间点
- 直接模拟 09:25 / 09:33 / 09:38 / 09:43 / 09:45 整套流程
- 用来验自动链是否正常

## 输出内容
自动版输出的不是单一 JSON，而是按阶段输出：
- 竞价风向
- 第一轮初筛
- 第二轮筛选
- 强弱确认
- 上午主看名单

## 当前依赖关系
### 正式版
- `skills/a-share-opening-flow/scripts/opening_flow.py`

### 测试版
- `skills/a-share-opening-flow-v6-test/scripts/opening_flow_v6_test.py`

## 当前稳定性规则
- 东方财富默认禁用
- 正式版优先
- 测试版兜底
- Python 输出编码固定为 UTF-8

## 常见故障
### 1. dry-run 没内容
优先检查正式版 / 测试版是否能单独正常跑。

### 2. 某个时间点为空
先看正式版是否输出为空，再看测试版是否接管。

### 3. 中文乱码
当前已强制 UTF-8，换电脑若再出现乱码，优先检查终端和 Python 编码环境。

## 使用建议
- 明天盘中自动看盘：用这个
- 单独查实时盘面：用正式版
- 查逻辑偏差：用测试版