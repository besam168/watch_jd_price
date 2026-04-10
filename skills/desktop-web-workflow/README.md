# desktop-web-workflow

桌面网页操作工作流原型。

## 当前第一版脚本

### 发送“继续”到 OpenClaw Control 页面

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\desktop-web-workflow\scripts\send-openclaw-continue.ps1
```

## 当前能力
- 打开本地 OpenClaw Control 页面
- 聚焦 OpenClaw 窗口
- 截图保存
- OCR 结果归档
- 在当前光标位置点击一次
- 输入 `继续`
- 回车发送
- 再截图归档
- 输出本次运行日志路径

## 注意
这还是第一版原型：
- 目前默认依赖**当前鼠标已经在输入框附近**或窗口焦点已对准可输入区域
- 下一版会补：
  - 输入框区域 OCR/坐标定位
  - 多次点击/Tab 聚焦 fallback
  - 成功输出更明确的 OCR 判定
