# scheduled-report-mailer / 新闻项目维护说明

## 当前固定执行标准
详见：
- `REPORT_STANDARDS.md`
- `OPS_CHECKLIST.md`（运维检查清单：按模块优先级 + 失败回退）

当前报告项目后续应统一按这份标准执行，核心包括：
- 固定采集标准（0–24小时、重点源白名单）
- 固定输出标准（标题、结构、溯源、禁止虚构）
- 固定核查清单（市场、地缘、内容质量）
- **内容命中口径：国际时事新闻可作为有效候选，之后再进入 evidence gate 判断**

## 项目作用
这套项目负责：
- 收集新闻与市场数据
- 生成中文报告
- 发送邮件
- 记录状态与日志
- 必要时触发桌面浏览器 fallback

## 默认上线策略（当前生效基线）
- 质量门策略：`send_with_warning`
  - 当前配置位置：`config/report-config.json` -> `delivery_policy.send_on_partial = "send_with_warning"`
  - 当前已观察到的运行行为（以日志为准）：
    - `pass`：正常发送
    - `partial`：**允许发送，但会附 warning / 质量提示**
    - `fail`：阻断发送（返回 `JOB_BLOCKED_AT_FAIL`）
- 说明：
  - 若未来切回 `strict_block` / `block`，必须同步更新 `report-config.json`、本 README、`OPS_CHECKLIST.md`，并保留一轮最小真测日志作为验收证据。
- 桌面 fallback：`conditional_trigger`
  - 配置位置：`config/report-config.json` -> `desktop_fallback`
  - 触发信号：
    - 质量门非 pass
    - 头条数不足 / 证据数不足
    - 出现占位搜索发现
    - 报告中出现“今日无额外摘要”标记

## 运行命令（验收用）
在 `C:\Users\besam\.openclaw\workspace` 下执行：

```bash
# 语法检查
python -m py_compile skills/scheduled-report-mailer/scripts/run-job.py skills/scheduled-report-mailer/scripts/desktop-fallback.py

# 仅采集+评估（不发信）
python skills/scheduled-report-mailer/scripts/run-job.py --job comprehensive-morning --collect-only

# 全链路（采集 -> 评估 -> 条件fallback -> 发信）
python skills/scheduled-report-mailer/scripts/run-job.py --job comprehensive-morning
```

## 关键状态与日志
- 主状态：`state/last-comprehensive-morning.json`
- 评估结果：`state/report-evaluation.json`
- fallback执行状态：`state/desktop-fallback-status.json`
- 运行日志：`logs/comprehensive-morning.log`

日志中会明确写出：
- `DESKTOP_FALLBACK_DECISION`（是否触发 + 原因）
- `DESKTOP_FALLBACK`（fallback执行结果）
- `EVALUATE_AFTER_FALLBACK`（fallback后复评）

## 失败恢复 / 回滚开关
- 临时关闭 fallback：`desktop_fallback.enabled = false`
- 强制始终触发 fallback：`desktop_fallback.mode = "always"`
- 切到“部分通过阻断发送”：`delivery_policy.send_on_partial = "block"`
- 当前默认基线：`delivery_policy.send_on_partial = "send_with_warning"`

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
