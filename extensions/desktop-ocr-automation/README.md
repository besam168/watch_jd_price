# OpenClaw 桌面 OCR 自动化插件

> 交接清单和完整使用说明见：`HANDOVER_OPENCLAW.md`

这是给 OpenClaw 使用的 Windows 插件：在 Windows 主屏幕上做中文 OCR 识别，并按识别到的文字自动点击。

当前版本按你的要求做了最小可用版：

1. PaddleOCR 中文识别；
2. 根据文字自动点击；
3. 桌面 `run.bat` 一键启动；
4. debug 截图和日志；
5. 只操作主屏幕，不操作副屏。

---

## 目录

```text
desktop-ocr-automation
├─ openclaw.plugin.json       OpenClaw 插件清单
├─ index.ts                   OpenClaw 工具入口
├─ desktop_ocr_agent.py       OCR/点击主程序
├─ config.json                配置
├─ run.bat                    双击输入文字并执行 OCR 点击
├─ scan_only.bat              双击只识别屏幕，不点击
├─ install_plugin_deps.bat    一键安装插件 Node 依赖 + Python 依赖
├─ install_deps.bat           安装 Python 依赖
├─ screenshots\              截图和 debug 标注图
└─ logs\                     日志和 OCR JSON 结果
```

---

## 第一次使用

插件目录：

```bat
cd /d C:\Users\besam\.openclaw\workspace\extensions\desktop-ocr-automation
```

先安装依赖；最简单是直接双击或运行：

```bat
install_plugin_deps.bat
```

也可以分步安装 Node 依赖（用于 OpenClaw 插件入口）：

```bat
npm install
```

再安装 Python OCR 依赖：

```bat
install_deps.bat
```

或手工执行：

```bat
python -m pip install "paddlepaddle==3.2.2" paddleocr pyautogui pillow opencv-python "numpy<2.4,>=1.24"
```

PaddleOCR 第一次运行会下载模型，可能比较慢。

---

## OpenClaw 工具

插件注册两个工具：

- `desktop_ocr_scan_primary`：只截主屏并 OCR，不点击；
- `desktop_ocr_click_text`：按文字查找并点击，参数 `click=false` 或省略时只 dry-run，`click=true` 才真实点击；
- `desktop_ocr_click_text` 还支持：
  - `failIfMultiple=true`：匹配到多个候选时直接失败，避免误点；
  - `listMatches=true`：把所有匹配候选一起列出来，方便人工确认。

示例意图：

```text
用 desktop_ocr_scan_primary 扫描主屏幕。
用 desktop_ocr_click_text 查找“确定”，先 dry-run。
用 desktop_ocr_click_text 查找“确定”，listMatches=true。
用 desktop_ocr_click_text 查找“确定”，failIfMultiple=true。
用 desktop_ocr_click_text 查找“确定”，click=true 真实点击。
```

如果 OpenClaw 需要手动加载本地插件，请把插件路径加入 OpenClaw 的插件加载路径，路径为：

```text
C:\Users\besam\.openclaw\workspace\extensions\desktop-ocr-automation
```

---

## 只识别主屏幕

本工具只截取 Windows 主屏幕区域：

```text
bbox = (0, 0, 主屏宽度, 主屏高度)
```

副屏不会被截图，也不会被点击。

注意：如果 Windows 把副屏设置成“主显示器”，那工具会操作那个被 Windows 标记为主显示器的屏幕。请在 Windows 显示设置里确认主屏幕。

---

## 最安全的测试方式：只扫描不点击

```bat
scan_only.bat
```

或：

```bat
python desktop_ocr_agent.py --scan
```

会生成：

```text
screenshots\latest_primary.png       主屏截图
screenshots\latest_debug.png         OCR 标注图
logs\latest_ocr_results.json         OCR 文字和坐标
logs\run.log                         运行日志
```

---

## dry-run：看它会点哪里，但不真实点击

默认配置里 `dry_run=true`，所以直接运行不会真实点击：

```bat
run.bat
```

输入目标文字，例如：

```text
确定
```

或命令行：

```bat
python desktop_ocr_agent.py --text 确定
```

输出会显示：

```text
将点击(dry-run): text='确定' conf=0.98 screen=(x,y)
```

如果你想同时把所有候选也列出来，便于确认多个同名按钮：

```bat
python desktop_ocr_agent.py --text 确定 --list-matches
```

确认位置正确后，再真实点击。

---

## 多候选安全模式

如果屏幕上可能同时出现多个相同/相近文字，建议先用下面命令避免误点：

```bat
python desktop_ocr_agent.py --text 确定 --list-matches --fail-if-multiple
```

行为说明：

- `--list-matches`：列出全部匹配候选；
- `--fail-if-multiple`：若匹配到多个候选，直接停止，不执行点击；
- 适合“确定 / 登录 / 发送 / 保存”这类常见重复文字场景。

---

## 真实点击

加 `--click`：

```bat
python desktop_ocr_agent.py --text 确定 --click
```

匹配方式默认是包含匹配，比如目标 `确定` 可以匹配 `确定(&O)`。

可选匹配方式：

```bat
python desktop_ocr_agent.py --text 确定 --match exact --click
python desktop_ocr_agent.py --text "确.*" --match regex --click
```

---

## 桌面图标使用

可以把 `run.bat` 发送到桌面快捷方式：

1. 右键 `run.bat`；
2. 选择“发送到”；
3. 选择“桌面快捷方式”。

以后你用手机远程控制电脑时，只要点这个桌面图标即可。

---

## 配置文件

`config.json`：

```json
{
  "screen": {
    "mode": "primary",
    "note": "只操作 Windows 主屏幕；副屏不会被截图或点击"
  },
  "ocr": {
    "lang": "ch",
    "use_angle_cls": true,
    "confidence_min": 0.55
  },
  "click": {
    "move_duration": 0.15,
    "after_click_sleep": 0.5,
    "fail_if_multiple": false
  },
  "default_task": {
    "target_text": "确定",
    "match_mode": "contains",
    "dry_run": true
  }
}
```

如果你想默认就真实点击，把：

```json
"dry_run": true
```

改成：

```json
"dry_run": false
```

但建议保留 `true`，真实点击时显式加 `--click` 更安全。

---

## 失败排查

### 1. 找不到文字

先运行：

```bat
python desktop_ocr_agent.py --scan
```

查看：

```text
screenshots\latest_debug.png
logs\latest_ocr_results.json
```

确认 OCR 有没有识别到目标文字。

### 2. 点击位置不对

查看：

```text
screenshots\latest_debug.png
```

绿色框是 OCR 识别区域，红色框是目标匹配区域。

### 3. 中文识别差

确认用的是 PaddleOCR 中文模型：

```json
"lang": "ch"
```

第一次运行模型下载失败时，重新运行 `install_deps.bat` 或检查网络。

---

## 当前限制

- 只做文字 OCR 点击，不做图标模板匹配；
- 只操作主屏；
- 不处理管理员权限窗口里的鼠标/键盘限制；
- 默认只点击最高置信度匹配项；
- 不会跨步骤执行复杂流程，后续可以扩展 tasks JSON。
