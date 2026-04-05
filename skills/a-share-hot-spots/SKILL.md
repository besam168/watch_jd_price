---
name: a-share-hot-spots
description: 跟踪中国A股实时行情、主要指数、热点板块与龙头股。适用于查询单只A股、查看大盘、查看概念热点、快速生成盯盘摘要。使用本地 Python 脚本抓取新浪财经与东方财富公开行情接口，不安装第三方可疑 skill 包。
---

# a-share-hot-spots

用于中国 A 股市场的轻量实时追踪。

## 适用场景
- 用户要查某只 A 股：如“查下 600519”
- 用户要看大盘：如“今天 A 股怎么样”“看下指数”
- 用户要看热点板块：如“今天最强板块”“热点概念有哪些”
- 用户要快速盯盘摘要：如“给我一个 A 股盘面快照”

## 默认做法
优先调用脚本：

```powershell
python {baseDir}/scripts/market_watch.py --summary
```

查个股：

```powershell
python {baseDir}/scripts/market_watch.py --code 600519 000001
```

查指数：

```powershell
python {baseDir}/scripts/market_watch.py --index
```

查热点板块：

```powershell
python {baseDir}/scripts/market_watch.py --hot-sectors
```

## 输出原则
- 中文输出
- 直接给结果，不讲废话
- 抓不到的数据直接明说，不编造
- 如果接口异常，说明是数据源失败，不要假装成功

## 备注
- 当前版本优先做稳：个股、指数、热点板块
- 后续如需要，再扩展热门股、连板股、北向资金、涨停池等
