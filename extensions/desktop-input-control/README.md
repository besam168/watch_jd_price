# Desktop Input Control

本地 Windows 桌面输入控制扩展。

## 当前阶段
现在已经从“二期稳态版”继续推进到**三期增强版**：
- 输入控制可用
- OCR 找字可用
- 安全护栏可用
- 动作日志可用
- 点击后校验可用
- 新增窗口列表/绑定
- 新增失败重试
- 新增点击前后截图归档

## 已完成功能

### 输入控制
- 绝对坐标鼠标移动 `desktop_mouse_move`
- 相对鼠标移动 `desktop_mouse_move_relative`
- 鼠标点击 `desktop_mouse_click`
  - `left`
  - `right`
  - `middle`
  - `double`
- 鼠标拖拽 `desktop_mouse_drag`
- 鼠标滚轮 `desktop_mouse_scroll`
- 文本输入 `desktop_type_text`
- 快捷键触发 `desktop_press_hotkey`
- 打开应用 `desktop_open_app`
- 打开 URL `desktop_open_url`
- 运行命令 `desktop_run_command`（默认关闭，需在 `safe-config.json` 显式放开）
- 窗口聚焦 `desktop_focus_window`
- 窗口列表读取 `desktop_list_windows`
- 当前前台窗口读取 `desktop_get_foreground_window`
- 当前窗口锁读取 `desktop_get_window_lock`
- 设置窗口锁 `desktop_set_window_lock`
- 清除窗口锁 `desktop_clear_window_lock`
- 最近动作日志读取 `desktop_get_recent_actions`

### 屏幕感知
- 截图 `desktop_screen_capture`
- OCR 识别 `desktop_screen_ocr`
- 查找屏幕文字 `desktop_find_text_on_screen`
- 查找并点击屏幕文字 `desktop_click_text_on_screen`
  - 支持 `dryRun`
  - 支持点击后 `verifyQuery`
  - 支持点击后 `verifyAbsentQuery`
  - 支持 `verifyDelayMs`
  - 支持 `retries`
  - 支持 `retryDelayMs`
  - 支持 `archiveScreenshots`
  - 支持点击前先 `focusWindowTitle` / `focusWindowPid`

## 三期增强点

### 1) 更稳的窗口绑定
新增：
- `desktop_list_windows`
- `desktop_focus_window` 支持 `title` 或 `pid`
- `desktop_get_window_lock`
- `desktop_set_window_lock`
- `desktop_clear_window_lock`

这比单纯模糊标题匹配更稳，方便后续做“先锁定目标窗口，再操作”；窗口锁开启后，输入动作默认只允许打到被锁定窗口。

### 2) 重试机制
`desktop_click_text_on_screen` 现在支持：
- `retries`
- `retryDelayMs`

当 OCR 命中不稳、点击后验证失败时，可以自动重试，而不是一次失败就结束。

### 3) 点击前后截图归档
新增：
- `archiveScreenshots`

启用后会把点击前/后的截图自动保存到：
- `artifacts/`

这对复盘、调试、留证都非常有用。

## 二期保留能力

### 安全护栏
`safe-config.json`：
- `blockedWindowTitles`
- `allowedWindowTitles`
- `requireWindowMatchForInput`
- `allowCommands`
- `allowOpenApp`
- `allowOpenUrl`
- `allowTyping`
- `allowHotkeys`

默认策略：
- `run-command` 默认禁止
- 可对高风险窗口做前台阻断
- 可切成“只允许指定窗口接收输入”模式

### 动作日志
所有关键动作会写入：
- `logs/desktop-actions.jsonl`

记录内容包括：
- 时间
- 动作名
- 参数
- 执行结果
- 当前前台窗口

### 点击后校验
可再次截图 + OCR，用于判断：
- 某个目标文本是否出现
- 某个旧文本是否消失

## 结构
- `index.ts`：OpenClaw 工具注册入口
- `scripts/desktop-input.py`：输入控制主运行时（当前主线）
- `scripts/desktop-input.ps1`：旧版 PowerShell 原型
- `scripts/screen-capture-compat.ps1`：截图
- `scripts/screen-ocr.py`：OCR 与文字定位
- `safe-config.json`：安全配置
- `logs/`：动作日志
- `artifacts/`：截图归档
- `openclaw.plugin.json`：插件元数据

## 风险提示
这是高风险能力：
- 会直接影响桌面输入
- 可能触发真实点击/快捷键/命令执行
- 正式接入自动工作流时，强烈建议启用窗口白名单或显式确认

## 快速验证

### 本地直接验证
```powershell
python scripts/desktop-input.py get-foreground-window
python scripts/desktop-input.py list-windows chrome
python scripts/desktop-input.py set-window-lock chrome 0
python scripts/desktop-input.py get-window-lock
python scripts/desktop-input.py mouse-move 200 200
python scripts/desktop-input.py mouse-move-relative 50 20
python scripts/desktop-input.py mouse-click left
python scripts/desktop-input.py clear-window-lock
python scripts/desktop-input.py get-recent-actions 10
powershell -ExecutionPolicy Bypass -File scripts/screen-capture-compat.ps1
python scripts/screen-ocr.py scripts/capture-style-test.png chi_sim+eng --query 设置 --top-n 3
powershell -ExecutionPolicy Bypass -File scripts/demo-workflow.ps1
```

### OpenClaw 调用建议
更稳的调用顺序：
1. `desktop_list_windows`
2. `desktop_get_foreground_window`
3. `desktop_screen_capture`
4. `desktop_find_text_on_screen`
5. `desktop_click_text_on_screen`（先 `dryRun=true`）
6. 正式点击时带上 `verifyQuery` / `verifyAbsentQuery`
7. 需要时启用 `retries` + `archiveScreenshots`

## 推荐实战策略
不要盲点。优先用：
- 窗口列表确认
- 前台窗口确认
- OCR 找字
- dry-run
- 点击后校验
- 失败重试
- 截图归档
- 动作日志复盘

这 8 个组合起来，才更接近真正可落地的桌面自动化工具。
