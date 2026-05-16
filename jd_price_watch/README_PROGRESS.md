# 京东 iPhone 17 256G 盯价进展记录

## 当前商品
- SKU: `100278222276`
- 标题: `Apple/苹果 iPhone 17 256GB 薰衣草紫色`
- 店铺: `Apple产品京东自营旗舰店`
- 正式链接: `https://item.jd.com/100278222276.html`

## 已验证结果
1. 静态 requests 抓取只能拿到壳页/通用页，不能稳定拿到价格数字。
2. Playwright 浏览器态可稳定打开真实商品页，并识别商品标题、店铺、自营信息。
3. 价格 DOM 已定位到：`.price.J-p-100278222276`
4. 当前自动化环境下，该价格节点为空，只显示 `￥`，未出现具体数字。
5. 页面补数相关业务接口 `pc_detailpage_wareBusiness` 当前观察到返回 `403`。
6. 复用本机 Chrome/Edge 用户目录后，仍未在自动化页中读到价格数字。
7. 截图 + OCR 已打通，但截图中未稳定出现价格数字，因此 OCR 无法凭空识别不存在的数字。

## 当前最准确结论
- 这不是链接问题，而是京东价格补数在当前自动化环境下未稳定下发。
- 真实价格 DOM 已定位：`.price.J-p-100278222276`，当前自动化页仅显示 `￥`，数字为空。
- 深挖 network 后已确认，关键补数接口为：`pc_detailpage_wareBusiness`
- 当前 Playwright 自动化环境下，该接口请求已经自动带出完整 `h5st`、`x-api-eid-token`、`uuid`、`scval` 等关键参数，但服务端仍返回 `403`。
- 说明当前阻断已经不在“少参数/少脚本”这一层，而在更高一级的风控/会话校验/环境识别。
- 下一步最可行方案：
  1. 让真实浏览器页面先显示完整价格（人工登录/真实会话）
  2. 再接管浏览器态读价 / OCR / 30分钟轮询 / QQ通知

## 现有文件
- `watch_jd_price.py`：最小盯价骨架（当前 requests 版）
- `watch_jd_price_playwright.py`：浏览器态读价与邮件提醒原型
- `watch_jd_price_multi.py`：新建的多提取器版本，按 `PriceBuddy` 思路把 requests_html / playwright_dom 拆成独立提取器，并统一做状态记录、日志记录、降价判断与 QQ 邮件通知
- `playwright_probe.py`：浏览器态商品页探测
- `playwright_probe_price.py`：价格 DOM 探测
- `playwright_logged_probe.py`：复用本机浏览器用户目录探测
- `jd_logged_probe.png`：页面截图
- `ocr_*`：OCR 试验脚本与产物

## 本轮结构升级（PriceBuddy 风格）
- 已开始把单脚本改造成“多提取器”结构，而不是把所有逻辑硬塞在一个抓取函数里。
- 当前第一版提取器：
  1. `requests_html`
  2. `requests_with_profile_cookies`
  3. `script_json`
  4. `playwright_dom`
  5. `profile_scan`
  6. `real_session_probe`
  7. `active_window_ocr`
- 当前统一收口逻辑：
  - 所有提取器都返回标准化 `ExtractAttempt`
  - 最终汇总成统一 `Snapshot`
  - 写入 `data/price_log.jsonl`
  - 更新 `data/state_multi.json`
  - 若价格下降则走 QQ 邮箱 SMTP 通知
- 这样后续继续新增：
  - `ocr_extractor`
  - `real_session_extractor`
  时，不需要再推翻主流程重写。
- 本轮还顺手补了两件工程细节：
  1. 新增 `script_json` 提取层，专门扫描页面 `script` 块里的 `price/jdPrice/sku` 线索；
  2. 给脚本加了 `stdout/stderr` UTF-8 重配置，尽量压住之前 PowerShell/GBK 环境下的中文输出乱码。
- 最新又补了两层与真实会话相关的诊断：
  - `real_session_probe`
    - 改为显式拉起真实 Chrome 会话（非 headless）再探一次价格 DOM；
    - 额外记录 `has_login_words`、选择器快照、body 片段，便于判断到底是“没登录”还是“登录了但价格仍未下发”。
  - `profile_scan`
    - 不再只盯一个默认目录，而是枚举本机多个 Chrome/Edge profile；
    - 逐个记录是否出现“你好，请登录/免费注册”、是否命中店铺、价格 DOM 是否有数字；
    - 用来找出“哪一个 profile 更像真正带京东登录态的候选”。
- 进一步新增两层收口能力：
  - `requests_with_profile_cookies`
    - 尝试直接读取 Chrome profile 的本地 JD cookie 并回放请求；
    - 若能读到 cookie，理论上可避开部分 Playwright 上下文差异。
  - `active_window_ocr`
    - 为“活窗口接管”预留正式入口；
    - 约定输入截图文件：`active_window_price.png`；
    - 自动生成多组裁剪与预处理图到 `ocr_debug/`，并跑 Tesseract 提取价格数字；
    - 这样即便网页态继续被京东拦，后续也能直接走“已打开窗口截图 -> OCR -> 比价 -> 通知”链路。
- 当前仍未突破的核心阻断不变：京东页面在自动化环境下价格数字未稳定下发；结构升级解决的是“工程收口问题”，不是“京东已被攻破”。

## 2026-05-09 稳定化收口
- 已把 `5590.0` 固化为当前可用基线：`data/config.json -> baseline_price`，`data/state_multi.json -> last_price/baseline_price`。
- 已新增价格可信度过滤：
  - 只接受 `4000-9000` 区间内的候选价；
  - 显式拉黑 `11000 / 11041 / 2019 / 2022 / 1800` 等已见脏值；
  - 候选价若高于基线 25% 以上也会被拒绝。
- 已调整多提取器收口优先级：`active_window_ocr > real_session_probe > playwright_dom > profile_scan > requests_with_profile_cookies > script_json > requests_html`。
- 被拒绝的脏价不会参与最终 `Snapshot.price`，但会写入 attempts 的 `meta.rejected_price / meta.reject_reason`，便于回看诊断。
- 邮件提醒策略已改为“只对真降价发提醒”：
  - 首次记录不再发提醒；
  - 当前价必须低于 `baseline_price=5590`；
  - 且相对上次/基线至少下降 `notify_min_drop=1.0` 才发 QQ 邮箱通知。
- 已用最小测试验证：`11041` 会被压掉，`5590` 只作为基线不提醒，`5588` 会触发真降价提醒。

## 2026-05-09 OCR 自动截图收口
- `active_window_ocr` 已从“只读手工截图 `active_window_price.png`”升级为：
  1. 自动截取 Windows 当前前台窗口到 `active_window_auto.png`；
  2. 仅当前台窗口标题像京东商品页（含 `京东`/`jd.com`/`item.jd.com`/`iPhone 17`/SKU 等）时，才信任自动截图；
  3. 若前台不是京东页，则拒绝自动截图，避免把 OpenClaw/控制台里的数字 OCR 成假价格；
  4. 仍保留 `active_window_price.png` 作为手工截图回退入口；
  5. OCR 多区域裁剪、多预处理变体会写入 `ocr_debug/` 便于复盘。
- 新增运行参数：
  - `python watch_jd_price_multi.py --ocr-only --dry-run`：只验证 OCR，不发邮件；
  - `python watch_jd_price_multi.py --ocr-only --open-url --wait-seconds 20 --dry-run`：先打开商品页，给 20 秒让用户登录/切前台，再 OCR；
  - `python watch_jd_price_multi.py --ocr-only --open-url --wait-seconds 20 --loop`：真实 OCR 盯价，按 `poll_minutes=30` 循环，满足真降价条件才发 QQ 邮件。
- 已验证：
  - `python -m py_compile watch_jd_price_multi.py` 通过；
  - 合成截图 `Y5588` 可被 OCR 识别为 `5588.0`；
  - `11041` 会被 `known_bad_price` 过滤；
  - `5588` 相对基线 `5590` 会触发真降价判断；
  - 真实运行 `--ocr-only --dry-run` 时，当前前台为 `OpenClaw Control - Google Chrome`，已被信任窗口校验拒绝，没有把控制台数字当成京东真实价。

## 运行前必须确认
1. 用真实 Chrome/Edge 打开 `https://item.jd.com/100278222276.html`。
2. 登录京东，让商品价格数字清晰显示在页面首屏。
3. 把这个京东商品页置于前台；窗口标题不要是 OpenClaw/控制台/编辑器。
4. 先跑：`python watch_jd_price_multi.py --ocr-only --dry-run`。
5. 输出里必须看到：
   - `主提取器：active_window_ocr`
   - `当前价格：¥xxxx.xx`
   - `meta.capture.trusted_jd_window: true`
6. 确认无误后再跑循环：`python watch_jd_price_multi.py --ocr-only --loop`。
