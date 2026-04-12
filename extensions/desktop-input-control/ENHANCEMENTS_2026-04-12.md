# desktop-input-control 增强说明（2026-04-12）

本次基于 `clawhub` 上的 `desktop-control` 思路，补强了原有 `extensions/desktop-input-control`，但没有照搬其“AI agent”包装层。

## 新增能力

### 1. 模板图像匹配
新增工具：
- `desktop_find_image_on_screen`
- `desktop_click_image_on_screen`

用途：
- 先截图当前屏幕
- 用 OpenCV 模板匹配查找指定图片
- 返回坐标、中心点、匹配分数
- 可直接点击目标图片中心点

### 2. 底层脚本新增动作
`desktop-input.py` 新增：
- `find-image`

## 设计原则

- 保留原有 OCR / 文本点击 / 窗口锁 / 焦点校验这套更实战的能力
- 只吸收商店 skill 中真正有价值的“轻视觉”部分
- 不引入未做实的“自然语言自主规划 / 游戏代理 / 假智能层”

## 当前组合后的能力闭环

现在这个桌面扩展同时支持：
- 坐标点击
- 文本 OCR 查找点击
- 模板图片查找点击
- 窗口聚焦与锁定
- 输入 / 快捷键 / 滚轮 / 拖拽

## 依赖说明

图像模板匹配依赖：
- `opencv-python`
- `numpy`

如果本机缺失，`find-image` 会明确报错，不影响原有 OCR 与桌面控制能力。
