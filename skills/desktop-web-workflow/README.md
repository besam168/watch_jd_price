# desktop-web-workflow

桌面网页操作工作流原型。

## 当前脚本1：窗口内相对坐标版

```powershell
python .\skills\desktop-web-workflow\scripts\script1_runner.py
```

默认行为：
- 不开网页
- 不改浏览器大小位置
- 查找 `OpenClaw Control` 窗口
- 移动到窗口内采样得到的相对坐标
- 点击输入框区域
- 输入 `继续`
- 回车发送

## 当前脚本1采样点
- 窗口查询：`OpenClaw Control`
- 相对点击点：`(833, 943)`

## 使用约定
执行前请先：
- 自己把 OpenClaw Control 页面打开好
- 保持浏览器布局不要大幅改变

然后发送口令：
- `起动脚本1`

## 当前能力
- 目标窗口识别
- 窗口内相对坐标点击
- 文本输入
- 回车发送
- 运行日志归档

## 后续待补
- 多点回退
- OCR 校验是否进入输入框
- 成功回读校验
