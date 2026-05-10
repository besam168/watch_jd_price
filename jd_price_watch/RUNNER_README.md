# JD iPhone 17 稳定常驻方案（Windows）

## 推荐入口
- 单次执行：`run_jd_price_watch_once.bat`
- 小时常驻：`run_jd_price_watch_hourly.bat`

## 方案说明
这套方案不依赖 OpenClaw 的临时后台 exec 会话，而是走本机 Windows 批处理常驻循环，更适合长期盯价。

## 当前固定行为
- 每轮先自动打开：`https://item.jd.com/100278222276.html`
- 每次尝试等待 20 秒
- 执行：`python watch_jd_price_multi.py --ocr-only`
- 若本轮未确认到京东商品页 / 未读到有效价格，会自动重试
- 单轮最多重试：3 次
- 只有真实价格跌破基线 `5999` 才发邮件
- 邮件只发：`besam168168@gmail.com`
- 小时版每轮间隔：3600 秒

## 当前加固点
- 不再只试 1 次；单轮失败会自动再次打开页面并重试
- 每次尝试后会读取 `data\state_multi.json`
- 若 `last_price` 为空或 `last_title` 仍是 `未知商品`，判定为本轮未确认成功，继续重试
- 每次尝试结果都会追加到 `logs\hourly_watch_runner.log`

## 日志
- `logs\hourly_watch_runner.log`
- `logs\last_attempt_status.txt`
- 业务状态：`data\state_multi.json`
- 业务流水：`data\price_log.jsonl`

## 手动启动
在 `jd_price_watch` 目录中直接双击：
- `run_jd_price_watch_once.bat`
- `run_jd_price_watch_hourly.bat`

## 后续更稳升级
如果要做真正系统级稳定常驻，下一步建议接 Windows 任务计划程序，让它在登录后自动启动 `run_jd_price_watch_hourly.bat` 或改成“每小时触发一次单次 bat”。
