# desktop-input-control

本地 Windows 桌面输入控制插件原型。

## 当前已实现
- 鼠标移动
- 鼠标左键/右键/双击
- 键盘输入文本
- 组合键触发（如 `ctrl+s`、`alt+tab`、`enter`）

## 插件目录
- `openclaw.plugin.json`
- `index.ts`
- `scripts/desktop-input.ps1`

## 当前工具名
- `desktop_mouse_move`
- `desktop_mouse_click`
- `desktop_type_text`
- `desktop_press_hotkey`

## 当前状态
- 已完成本地插件骨架
- 已实测 `mouse-move` 成功
- 当前属于第一版原型，后续可继续补：
  - 相对移动
  - 拖拽
  - 滚轮
  - 更稳的 Win 键/系统级快捷键处理
  - 安全确认机制

## 注意
这个插件是高风险输入控制能力。正式接入 OpenClaw 前，建议加白名单或显式确认机制。
