# 京东 iPhone 17 256G 盯价项目交接清单（给 OpenClaw）

## 1. 项目路径
项目目录：
`C:\Users\besam\.openclaw\workspace\jd_price_watch`

核心脚本：
`watch_jd_price_multi.py`

进展文档：
`README_PROGRESS.md`

配置文件：
`data\config.json`

状态文件：
`data\state_multi.json`

日志文件：
`data\price_log.jsonl`

---

## 2. 当前目标
监控京东站内：
`京东 iPhone 17 256G 自营价`

商品链接：
`https://item.jd.com/100278222276.html`

目标策略：
- 30 分钟轮询一次；
- 只在“可信真降价”时发 QQ 邮件；
- 价格必须来自可信路径，优先使用真实浏览器窗口截图 OCR；
- 当前可信基线价固定为：`5590.0`

---

## 3. 当前已完成内容

### 3.1 多提取器主流程已完成
主脚本：
`watch_jd_price_multi.py`

当前提取器优先级：
`active_window_ocr > real_session_probe > playwright_dom > profile_scan > requests_with_profile_cookies > script_json > requests_html`

说明：
- `active_window_ocr` 是最高优先级；
- 其他网络 / DOM 提取器保留为诊断和回退；
- 京东自动化环境下价格补数不稳定，所以不要单纯依赖 Playwright DOM 或 requests。

### 3.2 价格过滤逻辑已完成
已固化配置：
```json
{
  "baseline_price": 5590.0,
  "price_min": 4000.0,
  "price_max": 9000.0,
  "max_rise_pct_from_baseline": 0.25,
  "known_bad_prices": [11000.0, 11041.0, 2019.0, 2022.0, 1800.0],
  "only_notify_below_baseline": true,
  "notify_min_drop": 1.0,
  "suppress_first_record_notice": true
}
```

过滤规则：
- 低于 4000 拒绝；
- 高于 9000 拒绝；
- `11000 / 11041 / 2019 / 2022 / 1800` 明确拉黑；
- 高于基线 `5590` 的 25% 以上拒绝；
- 被拒绝价格会写入 attempt meta：
  - `rejected_price`
  - `reject_reason`

### 3.3 邮件提醒逻辑已完成
只在以下条件全部满足时提醒：
- 当前价有效；
- 当前价低于 `baseline_price=5590.0`；
- 相对上次价格 / 基线至少下降：`notify_min_drop = 1.0`
- 首次记录不提醒。

示例：
- `5590`：不提醒；
- `5588`：提醒；
- `11041`：过滤，不提醒。

---

## 4. OCR 当前状态

### 4.1 已实现内容
`active_window_ocr` 已从“只读手工截图”升级为：
- 自动截取 Windows 当前前台窗口；
- 截图保存为：`active_window_auto.png`；
- 仍保留手工截图回退入口：`active_window_price.png`；
- 自动生成 OCR 调试裁剪图到：`ocr_debug\`；
- 使用 Tesseract OCR：`C:\Program Files\Tesseract-OCR\tesseract.exe`；
- 对截图做多个区域裁剪和图像预处理：灰度、高对比、锐化、黑白阈值、京东价格区域裁剪、全窗口兜底裁剪。

### 4.2 重要安全保护
已经加了“可信京东窗口标题校验”。
自动截图只在当前前台窗口标题像京东商品页时才被信任。

信任关键词包括：
`京东 / jd.com / item.jd.com / iphone 17 / apple / 100278222276`

会拒绝的窗口关键词包括：
`openclaw / tanzo / visual studio code / cmd.exe / powershell`

原因：
曾真实 dry-run 时，前台窗口是：
`OpenClaw Control - Google Chrome`
OCR 一度识别出 `5258`；
但这不是京东真实价格，而是 OpenClaw 控制页里的数字；
所以已经补了窗口信任校验，并把状态回滚到基线 `5590.0`。

---

## 5. 当前验证结果

### 5.1 语法验证
已通过：
`python -m py_compile watch_jd_price_multi.py`

### 5.2 OCR 合成图验证
合成截图中写入：`Y5588`
OCR 可识别为：`5588.0`

### 5.3 价格过滤验证
已验证：
- `11041 -> 被拒绝，原因 known_bad_price`
- `5588 -> 有效，且相对 5590 触发真降价判断`

### 5.4 真实 dry-run 验证
运行过：
`python watch_jd_price_multi.py --ocr-only --dry-run`

当时结果：
- 当前前台窗口：`OpenClaw Control - Google Chrome`
- 脚本正确拒绝：`trusted_jd_window: false`
- `No screenshot available`

结论：
- OCR 流程可运行；
- 安全校验生效；
- 但当时没有京东真实商品页在前台，所以没有拿到可信真实京东价格。

---

## 6. 当前状态文件
状态文件：`data\state_multi.json`

当前应保持为：
```json
{
  "last_price": 5590.0,
  "baseline_price": 5590.0,
  "last_title": "active_window_ocr_trust_guard_verified",
  "last_store_text": "",
  "last_in_stock": null,
  "last_fetched_at": "2026-05-09 12:35:56",
  "last_extractor": "active_window_ocr",
  "last_note": "OCR dry-run completed; non-JD foreground window rejected; baseline preserved"
}
```

注意：
- 不要把之前 OCR 出来的 `5258` 当真实价；
- 那次来自 OpenClaw 控制页，已判定不可信。

---

## 7. 真实运行步骤

### 7.1 先做 dry-run
进入项目目录：
`cd C:\Users\besam\.openclaw\workspace\jd_price_watch`

运行：
`python watch_jd_price_multi.py --ocr-only --open-url --wait-seconds 20 --dry-run`

20 秒等待期间，需要人工确认：
- 浏览器打开京东商品页；
- 已登录京东；
- 商品价格数字清晰显示在首屏；
- 京东商品页在最前台；
- 前台窗口标题不是 OpenClaw / 控制台 / 编辑器。

### 7.2 dry-run 成功标准
输出里必须看到：
- `主提取器：active_window_ocr`
- `当前价格：¥xxxx.xx`

并且 meta 里必须有：
`"trusted_jd_window": true`

如果看到：
`"trusted_jd_window": false`
说明前台不是可信京东页，不能启动正式循环。

### 7.3 正式循环
确认 dry-run 价格可信后，运行：
`python watch_jd_price_multi.py --ocr-only --open-url --wait-seconds 20 --loop`

说明：
- 会按 `data\config.json` 中的 `poll_minutes=30` 循环；
- 只有低于 `5590.0` 且至少降 `1.0` 才发 QQ 邮件；
- 没有真降价只写日志和状态，不发邮件。

---

## 8. 常用命令
只跑 OCR 验证，不发邮件：
`python watch_jd_price_multi.py --ocr-only --dry-run`

打开京东页后等待 20 秒再 OCR：
`python watch_jd_price_multi.py --ocr-only --open-url --wait-seconds 20 --dry-run`

正式 30 分钟循环：
`python watch_jd_price_multi.py --ocr-only --open-url --wait-seconds 20 --loop`

语法检查：
`python -m py_compile watch_jd_price_multi.py`

---

## 9. OpenClaw 下一步应该做什么

### 必做 1：真实京东页前台 OCR 验证
请 OpenClaw 按以下步骤执行：
`cd C:\Users\besam\.openclaw\workspace\jd_price_watch`
`python watch_jd_price_multi.py --ocr-only --open-url --wait-seconds 20 --dry-run`

然后在 20 秒内：
- 登录京东；
- 打开商品页；
- 保证价格可见；
- 保证京东页在最前台。

检查输出是否：
- `trusted_jd_window: true`
- `当前价格：¥xxxx.xx`

### 必做 2：确认 OCR 价格是否等于肉眼看到的京东价格
如果 OCR 数字和肉眼价格一致，才可以正式循环。

如果不一致：
查看：
- `ocr_debug\`
- `active_window_auto.png`

检查截图区域是否包含价格；
必要时调整 `crop_variants()` 中京东价格区域裁剪框。

### 必做 3：启动正式循环
确认 dry-run 可信后：
`python watch_jd_price_multi.py --ocr-only --open-url --wait-seconds 20 --loop`

---

## 10. 风险点
- 不要信任非京东前台窗口 OCR；
- 当前已加校验，但如果京东窗口标题太特殊，可能需要补关键词；
- 不要把 `5258` 当真实价；
- 那次来自 OpenClaw 控制页，不是京东页面；
- 京东自动化 DOM 价格仍不稳定；
- `playwright_dom`、`real_session_probe` 可保留诊断，但当前主路径应是 `active_window_ocr`；
- OCR 只能识别截图里真实存在的数字；
- 如果京东页面没有显示价格，OCR 不可能拿到价格；
- 正式循环前必须先 dry-run；
- dry-run 通过后再允许发邮件。

---

## 11. 简短结论
当前代码层面 OCR 主路径已经做好：
`真实前台京东页截图 -> OCR -> 价格过滤 -> 真降价判断 -> QQ 邮件`

但当前还没有拿到可信京东真实价，因为最后一次真实运行时前台不是京东商品页，而是 OpenClaw 控制页。

OpenClaw 下一步只需要把真实京东商品页置前，先跑 `--ocr-only --dry-run`，确认 `trusted_jd_window=true` 且 OCR 价格和肉眼一致，然后再启动 `--loop`。
