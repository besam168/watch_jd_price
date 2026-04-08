# scheduled-report-mailer / 新闻项目维护说明

## 项目作用
这套项目负责：
- 收集新闻与市场数据
- 生成中文报告
- 发送邮件
- 记录状态与日志
- 必要时触发桌面浏览器 fallback

## 当前关键脚本
### 1. 主报告生成
- `daily_comprehensive_report.py`

### 2. 采集入口
- `collect_comprehensive_report.py`

### 3. 邮件发送入口
- `send_collected_comprehensive_report.py`

### 4. 桌面浏览器 fallback
- `desktop_browser_fallback.py`
- `desktop_browser_scroll.py`

## 当前已接入能力
### 主链
- RSS
- multi-search-engine 搜索发现
- 本地缓存页面 / markdown 抓取结果
- 市场快照补充

### 桌面 fallback
当前已接入：
1. 打开浏览器到目标 URL
2. 第一张截图：首屏
3. 轻微下拉
4. 第二张截图：下拉后内容
5. 分别 OCR
6. 标题校验
7. 状态结果写入 `reports/scheduled/desktop_browser_fallback.json`

## fallback 当前字段
- `screenshotPathTop`
- `screenshotPathScrolled`
- `ocrTop`
- `ocrScrolled`
- `ocrAvailable`
- `titleMatched`
- `ocrText`

## 采集状态
`collect_comprehensive_report.py` 当前会在状态里写入：
- 主采集结果
- 市场刷新结果
- `desktop_browser_fallback` 结果

## 当前已知规则
### 1. 市场数据
- 已补 A股 / 恒生 / 美股三大指数 / 日经 / FTSE 部分链路
- 仍有少量全球指数缺口，不可强行虚构

### 2. 桌面 fallback
- 只作为最后兜底，不取代主链
- 当前已支持两张截图与两次 OCR
- 若 OCR 结果混入桌面其它窗口内容，优先考虑浏览器置前与缩小识别范围

### 3. 报告写作原则
- 抓不到就明确写“今日无重大更新”
- 不用旧闻补洞
- 不伪造数据

## 常见问题
### 1. 报告里大量“今日无重大更新”
优先检查：
- 市场快照源是否成功
- 页面抓取是否拿到可信字段
- 桌面 fallback 是否已触发

### 2. OCR 识别到桌面其它内容
说明当前是整屏截图带来的杂项文字，需要后续继续优化浏览器内容区域识别。

### 3. 邮件链路正常但内容质量一般
优先继续优化：
- 头条发现层
- 市场数据链
- fallback 内容抽取质量

## 换电脑注意
- 先确认 Python 环境
- 先确认邮件配置
- 先确认截图脚本可用
- 先确认桌面 OCR 依赖脚本存在
- 桌面 fallback 依赖浏览器可被系统正常打开
