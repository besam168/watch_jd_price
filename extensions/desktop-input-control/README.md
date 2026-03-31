# Desktop Input Control

本地 Windows 桌面输入控制扩展。

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
- 运行命令 `desktop_run_command`
- 窗口聚焦 `desktop_focus_window`

### 屏幕感知
- 截图 `desktop_screen_capture`
- OCR 识别 `desktop_screen_ocr`
- 查找屏幕文字 `desktop_find_text_on_screen`
- 查找并点击屏幕文字 `desktop_click_text_on_screen`

## 结构
- `index.ts`：OpenClaw 工具注册入口
- `scripts/desktop-input.ps1`：鼠标/键盘/窗口控制
- `scripts/screen-capture-compat.ps1`：截图
- `scripts/screen-ocr.py`：OCR 与文字定位
- `openclaw.plugin.json`：插件元数据

## 当前定位
这已经不是“只能演示的原型”，而是一个可实际调用的 Windows 桌面输入控制扩展：
- 能控制鼠标和键盘
- 能截图
- 能 OCR 找字
- 能按文本定位并点击

## 风险提示
这是高风险能力：
- 会直接影响桌面输入
- 可能触发真实点击/快捷键/命令执行
- 正式接入自动工作流时，建议额外加确认、白名单或目标窗口限制

## 快速验证

### 本地直接验证
```powershell
python scripts/desktop-input.py mouse-move 200 200
python scripts/desktop-input.py mouse-move-relative 50 20
python scripts/desktop-input.py mouse-click left
powershell -ExecutionPolicy Bypass -File scripts/screen-capture-compat.ps1
python scripts/screen-ocr.py scripts/capture-style-test.png chi_sim+eng --query 设置 --top-n 3
```

### OpenClaw 调用建议
先走：
1. `desktop_screen_capture`
2. `desktop_find_text_on_screen`
3. `desktop_click_text_on_screen`（可先 `dryRun=true`）

这样更稳，不容易盲点。
