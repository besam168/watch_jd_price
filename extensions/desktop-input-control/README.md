# Desktop Input Control

本地 Windows 桌面输入控制扩展。

## 当前阶段
现在已经从“可用一版”升级到**二期稳态版方向**：
- 输入控制可用
- OCR 找字可用
- 新增安全护栏
- 新增动作日志
- 新增点击后校验能力

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
- 当前前台窗口读取 `desktop_get_foreground_window`
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

## 二期增强点

### 1) 安全护栏
新增 `safe-config.json`：
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

### 2) 动作日志
所有关键动作会写入：
- `logs/desktop-actions.jsonl`

记录内容包括：
- 时间
- 动作名
- 参数
- 执行结果
- 当前前台窗口

### 3) 点击后校验
`desktop_click_text_on_screen` 支持点击后再次截图 + OCR，用于判断：
- 某个目标文本是否出现
- 某个旧文本是否消失

这比“点完就算成功”稳得多。

## 结构
- `index.ts`：OpenClaw 工具注册入口
- `scripts/desktop-input.py`：输入控制主运行时（当前主线）
- `scripts/desktop-input.ps1`：旧版 PowerShell 原型
- `scripts/screen-capture-compat.ps1`：截图
- `scripts/screen-ocr.py`：OCR 与文字定位
- `safe-config.json`：安全配置
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
python scripts/desktop-input.py mouse-move 200 200
python scripts/desktop-input.py mouse-move-relative 50 20
python scripts/desktop-input.py mouse-click left
python scripts/desktop-input.py get-recent-actions 10
powershell -ExecutionPolicy Bypass -File scripts/screen-capture-compat.ps1
python scripts/screen-ocr.py scripts/capture-style-test.png chi_sim+eng --query 设置 --top-n 3
```

### OpenClaw 调用建议
更稳的调用顺序：
1. `desktop_get_foreground_window`
2. `desktop_screen_capture`
3. `desktop_find_text_on_screen`
4. `desktop_click_text_on_screen`（先 `dryRun=true`）
5. 正式点击时带上 `verifyQuery` 或 `verifyAbsentQuery`

## 推荐实战策略
不要盲点。优先用：
- 前台窗口确认
- OCR 找字
- dry-run
- 点击后校验
- 动作日志复盘

这 5 个组合起来，才接近“稳”。
