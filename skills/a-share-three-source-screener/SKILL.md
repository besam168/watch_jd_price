---
name: a-share-three-source-screener
description: 基于新浪实时行情、东方财富热榜/板块、腾讯历史月线（经 akshare）做三源共振筛股。适用于用户想找A股强势候选、盘中筛股、做热点与趋势交叉验证、快速输出候选名单时使用。
---

# a-share-three-source-screener

用三个数据口做一个更实战的 A 股候选筛选插件：
- **新浪财经**：个股实时行情、主要指数
- **东方财富**：热门股、概念板块、行业板块
- **腾讯历史（akshare 封装）**：月线历史数据与趋势/位置判断

## 适用场景
- 用户说“给我筛几个今天值得看的 A 股”
- 用户说“找下热点+趋势都不错的票”
- 用户说“盘中帮我抓几个强势候选”
- 用户说“把热点龙头里月线位置也一起看一下”

## 默认做法
优先跑候选扫描：

```powershell
python {baseDir}/scripts/three_source_screener.py --scan
```

如果要看更短的摘要：

```powershell
python {baseDir}/scripts/three_source_screener.py --brief
```

如果要只看热榜候选池：

```powershell
python {baseDir}/scripts/three_source_screener.py --pool
```

如果要查单只股票的三源评分：

```powershell
python {baseDir}/scripts/three_source_screener.py --code 600519
python {baseDir}/scripts/three_source_screener.py --name 万科A
```

如果要 JSON：

```powershell
python {baseDir}/scripts/three_source_screener.py --scan --json
```

## 筛选逻辑
默认按 3 个维度打分：
1. **实时强度**：涨幅、成交额、是否明显强于大盘
2. **热度归属**：是否进入热门股/热点板块/行业热点，是否属于热点龙头
3. **历史位置**：月线是否仍在相对低位、近几个月是否有放量抬升

## 输出原则
- 中文输出
- 先给结果，再给理由
- 数据源失败就明说，不装成功
- 候选名单以“可盯盘”优先，不夸成“必涨股”

## 备注
- 这个插件是对 `a-share-hot-spots` 的补充，不替代原插件
- 偏“候选筛选与排序”，不是全市场量化回测器
