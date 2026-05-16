# JD iPhone 17 Price Watch

一个用于监控京东 iPhone 17 256G 商品价格的本地脚本项目。

当前实现重点不是“随便抓到一个数字”，而是尽量只在**可信价格**出现且满足**真降价条件**时才触发提醒，避免把页面噪声、风控页、登录浮层或错误提取结果误当成真实价格。

## 当前监控商品

- 商品：Apple / 苹果 iPhone 17 256GB
- 渠道：京东
- SKU：`100278222276`
- 链接：<https://item.jd.com/100278222276.html>

## 项目结构

- `watch_jd_price_multi.py`：主脚本，多提取器版本
- `watch_jd_price.py`：较早的单脚本版本
- `watch_jd_price_playwright.py`：Playwright 原型版本
- `run_jd_price_watch_once.bat`：单次运行入口
- `run_jd_price_watch_hourly.bat`：Windows 小时循环入口
- `HANDOVER.md`：交接说明（偏内部）
- `RUNNER_README.md`：常驻运行说明
- `README_PROGRESS.md`：阶段性调试/进展记录

## 核心思路

这个项目不是单纯依赖某一种抓价方式，而是结合多种来源做提取与过滤：

- requests / HTML 结构提取
- 页面脚本数据提取
- Playwright DOM 提取
- 真实前台页面截图 OCR（更偏可信人工可见价格）

其中当前更强调：

> 真实可见页面价格 + 过滤规则 + 真降价判断

避免误把以下内容当成价格：

- 登录页/风控页噪声
- 页面上其它商品价格
- 推荐位价格
- 划线价/活动价碎片
- OCR 错位数字

## 环境要求

建议环境：

- Windows
- Python 3.10+
- Google Chrome（如果使用真实页面/Playwright 路线）
- Tesseract OCR（如果使用 OCR 路线）

如果你要跑 OCR 路线，需保证本机已安装 Tesseract，并且脚本中的路径可用。

## 快速开始

进入项目目录：

```bash
cd jd_price_watch
```

### 1）先做安全验证（不发通知）

```bash
python watch_jd_price_multi.py --ocr-only --dry-run
```

用途：
- 只验证 OCR / 当前可信页面取价是否正常
- 不发通知
- 适合先看脚本有没有把错误数字当真

### 2）先打开商品页，再做 dry-run

```bash
python watch_jd_price_multi.py --ocr-only --open-url --wait-seconds 20 --dry-run
```

用途：
- 自动打开商品页
- 预留 20 秒给你切到正确窗口 / 登录 / 确认页面
- 然后再做 OCR 检查
- 不发通知

### 3）正式循环监控

```bash
python watch_jd_price_multi.py --ocr-only --open-url --wait-seconds 20 --loop
```

用途：
- 打开页面
- 等待手动确认前台页面
- 进入循环盯价
- 满足真降价条件时才触发通知

## Windows 入口

### 单次运行

```bat
run_jd_price_watch_once.bat
```

### 小时循环运行

```bat
run_jd_price_watch_hourly.bat
```

当前小时 runner 的思路是：

- 每轮调用一次主脚本
- 间隔固定时间再次执行
- 适合本机常驻轻量运行

## 常用参数

主脚本 `watch_jd_price_multi.py` 当前可见的核心参数有：

- `--ocr-only`：只运行真实前台窗口截图 OCR，不跑其它网络/浏览器提取器
- `--once`：只运行一次（默认）
- `--loop`：循环运行
- `--open-url`：运行前先打开商品页
- `--wait-seconds`：运行前等待若干秒，方便手动登录/切前台
- `--dry-run`：不发送通知，只打印并写日志/状态

## 使用建议

推荐顺序：

1. 先跑 `--dry-run`
2. 确认当前窗口真的是京东商品页
3. 确认脚本拿到的价格和你肉眼看到的一致
4. 再切到正式循环

不要一上来就直接常驻发通知，不然容易把错误提取结果当成降价。

## 已知限制

1. 京东页面有风控、登录态、动态渲染等影响
2. 单纯 HTML / DOM / 脚本数据提取不一定总能代表真实到手价
3. 页面上可能出现多个数字，需要过滤规则判断哪个才是可信价格
4. OCR 也不是万能，前提是前台页面必须正确、清晰、无遮挡
5. 不同机器、不同浏览器状态、不同登录态，结果可能不一样

## 仓库内容说明

这个仓库适合保存：

- 核心脚本
- bat 启动入口
- 说明文档
- 调试思路和设计记录

不建议把以下本机运行产物直接提交进仓库：

- `data/`
- `logs/`
- `ocr_debug/`
- `ocr_focus/`
- `ocr_variants/`
- `__pycache__/`
- 截图 png
- probe 文本产物

这些内容通常只适合本机调试，不适合作为仓库主内容。

## 相关文档

- `HANDOVER.md`
- `RUNNER_README.md`
- `README_PROGRESS.md`

它们保留了这个项目在本机环境里的交接、运行与调试背景。

## 免责声明

本项目仅用于个人研究、自动化实验与价格监控流程验证。请自行评估目标网站使用规则、自动化访问风险及运行环境合规性。
