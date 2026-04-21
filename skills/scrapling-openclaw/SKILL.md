---
name: scrapling-openclaw
description: 使用本地 Scrapling 作为 OpenClaw 的主力网页抓取与资料抽取技能。适用于抓新闻、网页正文、文章列表、JS 渲染页面、需要更强伪装抓取时使用。支持静态抓取、动态浏览器抓取、stealthy 抓取，以及 html / markdown / text / json 输出。优先作为 firecrawl / web_fetch 的本地替代方案，但保留它们作为兜底。
---

# Scrapling OpenClaw

用本机已安装的 `scrapling` CLI 做网页抓取主力。

## 什么时候用
- 用户要抓新闻、文章、网页正文、资料页
- 提供一个或多个 URL，希望读正文
- `web_fetch` 抓不到、内容太脏、JS 渲染后才出现正文
- 需要更像浏览器的抓取方式
- 希望把网页转成 markdown / text 给 LLM 读

## 默认路由
按从轻到重的顺序选：

1. **静态抓取：`get`**
   - 适合大多数新闻页、博客、普通资料页
   - 速度最快

2. **动态抓取：`fetch`**
   - 页面依赖 JS 渲染
   - 需要等待选择器或网络空闲

3. **伪装抓取：`stealthy-fetch`**
   - 普通抓取容易被拦
   - 需要更强浏览器伪装

## 常用命令
```powershell
python {baseDir}/scripts/run_scrapling.py --url https://example.com --mode get --format md
python {baseDir}/scripts/run_scrapling.py --url https://example.com --mode fetch --format md --wait-ms 3000 --network-idle
python {baseDir}/scripts/run_scrapling.py --url https://example.com --mode stealthy --format md --ai-targeted
python {baseDir}/scripts/run_scrapling.py --url https://news.ycombinator.com --mode auto --format html
```

## 主力抓新闻建议
- **普通新闻正文**：`--mode auto --format md --ai-targeted`
- **新闻首页 / 栏目页 / 列表页**：`--mode get --format html`
- **正文是 JS 渲染**：`--mode fetch --format md --wait-ms 3000 --network-idle`
- **普通抓取被拦**：`--mode stealthy --format md --wait-ms 3000`
- **只抓正文局部**：补 `--css-selector "article, main, .article, .post-content"`

## 输出规则
- 默认输出到：`{baseDir}/output/`
- 同时把结构化结果写到 stdout JSON，便于 OpenClaw 直接读
- `content` 字段是主要正文
- `output_file` 是落盘文件路径
- `mode_used` 表示最终用了哪种抓取方式
- `fallbacks_tried` 记录失败后的降级/升级过程

## 参数建议
- 新闻正文：`--mode auto --format md --ai-targeted`
- 列表页/导航页：`--mode get --format html`
- JS 页面：`--mode fetch --format md --wait-ms 3000 --network-idle`
- 容易被拦的站：`--mode stealthy --format md --wait-ms 3000`

## 自动模式
`--mode auto` 的策略：
1. 先 `get`
2. 失败或内容太短，再 `fetch`
3. 仍失败，再 `stealthy`

## 注意
- 本技能优先本地抓取，但**不保证所有反爬站点都能过**。
- 如遇登录、点击、分页交互，仍要升级到 browser 类技能。
- 当前机器已安装 `scrapling`，但它会引入额外 Python 依赖；后续若影响别的脚本，要考虑虚拟环境隔离。
