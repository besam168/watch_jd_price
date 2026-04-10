# desktop-web-workflow

桌面网页操作工作流原型。

## 当前第一版脚本

### 脚本1：轻动作版发送消息

```powershell
python .\skills\desktop-web-workflow\scripts\script1_runner.py
```

默认行为：
- 不开网页
- 不聚焦窗口
- 不改变浏览器位置
- 在**当前鼠标位置**点击一下
- 输入 `继续`
- 回车发送

## 使用约定
执行前请先：
- 自己把 OpenClaw Control 页面打开好
- 把鼠标停在输入框里或输入框可点击位置

然后发送口令：
- `起动脚本1`

## 当前能力
- 轻动作点击
- 文本输入
- 回车发送
- 运行日志归档

## 后续待补
- 自定义消息内容
- OCR 定位输入框
- 成功回读校验
