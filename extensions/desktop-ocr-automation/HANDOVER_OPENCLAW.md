# OpenClaw 桌面 OCR 自动化插件交接清单与使用说明书

> 插件目录：`C:\Users\besam\.openclaw\workspace\extensions\desktop-ocr-automation`

---

## 1. 项目目标

这是一个给 OpenClaw 使用的 Windows 主屏幕 OCR 自动化插件。

核心能力：

1. 截取 Windows **主屏幕**；
2. 使用 PaddleOCR 中文模型识别屏幕文字；
3. 根据目标文字定位文字中心坐标；
4. 默认只 dry-run 显示将点击哪里；
5. 显式确认后才执行真实鼠标点击；
6. 保存截图、OCR 标注图、OCR JSON 和运行日志，方便排查。

---

## 2. 已交付文件清单

```text
desktop-ocr-automation
├─ openclaw.plugin.json       OpenClaw 插件清单
├─ index.ts                   OpenClaw 工具注册入口
├─ package.json               Node 脚本和依赖
├─ tsconfig.json              TypeScript 配置
├─ desktop_ocr_agent.py       OCR/点击主程序
├─ config.json                默认配置
├─ install_plugin_deps.bat    一键安装 Node + Python 依赖
├─ install_deps.bat           安装 Python 依赖
├─ run.bat                    输入文字后执行 OCR 点击，默认 dry-run
├─ scan_only.bat              只扫描主屏，不点击
├─ README.md                  插件说明
├─ HANDOVER_OPENCLAW.md       本交接清单和使用说明书
├─ screenshots\              截图和 OCR 标注图输出目录
└─ logs\                     日志和 OCR JSON 输出目录
```

---

## 3. OpenClaw 插件信息

### 插件路径

```text
C:\Users\besam\.openclaw\workspace\extensions\desktop-ocr-automation
```

### 插件清单

```text
openclaw.plugin.json
```

### 插件入口

```text
index.ts
```

### 注册工具

#### 3.1 `desktop_ocr_scan_primary`

用途：只截取主屏并执行 OCR，不点击。

适合场景：

- 先检查当前屏幕能识别出什么文字；
- 检查坐标是否在主屏；
- 检查 PaddleOCR 是否正常工作。

#### 3.2 `desktop_ocr_click_text`

用途：根据文字定位并点击。

参数：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---:|---|---|
| `text` | string | 是 | 无 | 要查找/点击的文字，例如 `确定` |
| `match` | string | 否 | `contains` | 匹配方式：`contains` / `exact` / `regex` |
| `click` | boolean | 否 | `false` | `false` 只 dry-run；`true` 才真实点击 |
| `failIfMultiple` | boolean | 否 | `false` | 为 `true` 时，如果匹配到多个候选则直接失败，不自动选最高置信度 |
| `listMatches` | boolean | 否 | `false` | 为 `true` 时，输出所有匹配候选，方便人工确认 |

安全规则：

- `click=false` 或省略：只输出将点击位置，不真实点击；
- `click=true`：真实移动鼠标并点击；
- `failIfMultiple=true`：遇到多候选时直接停止，适合高风险按钮。

---

## 4. 安装依赖

进入插件目录：

```bat
cd /d C:\Users\besam\.openclaw\workspace\extensions\desktop-ocr-automation
```

推荐一键安装：

```bat
install_plugin_deps.bat
```

也可以分步安装。

Node 依赖：

```bat
npm install
```

Python 依赖：

```bat
install_deps.bat
```

或手工执行：

```bat
python -m pip install "paddlepaddle==3.2.2" paddleocr pyautogui pillow opencv-python "numpy<2.4,>=1.24"
```

注意：当前 Windows 环境已验证 `paddlepaddle==3.2.2` 可运行。`paddlepaddle 3.3.1` 在本机曾触发 oneDNN 底层报错，不建议升级。

---

## 5. 命令行使用说明

### 5.1 只扫描主屏，不点击

```bat
python desktop_ocr_agent.py --scan
```

或双击：

```text
scan_only.bat
```

输出文件：

```text
screenshots\latest_primary.png       最新主屏截图
screenshots\latest_debug.png         最新 OCR 标注图
logs\latest_ocr_results.json         最新 OCR 文字、置信度、坐标
logs\run.log                         运行日志
```

### 5.2 dry-run 查找文字，不点击

```bat
python desktop_ocr_agent.py --text 确定
```

或显式写：

```bat
python desktop_ocr_agent.py --text 确定 --dry-run
```

成功时会输出类似：

```text
将点击(dry-run): text='确定' conf=0.98 screen=(x,y)
当前是 dry-run，没有真实点击。确认无误后可加 --click 执行真实点击。
```

如果想查看所有候选：

```bat
python desktop_ocr_agent.py --text 确定 --list-matches
```

### 5.3 多候选安全模式

如果你担心屏幕上有多个相同文字，建议先这样跑：

```bat
python desktop_ocr_agent.py --text 确定 --list-matches --fail-if-multiple
```

这时：

- 会列出全部候选；
- 若候选数大于 1，会直接停止；
- 不会自动选最高置信度去点。

### 5.4 真实点击

确认 dry-run 坐标正确后，再执行：

```bat
python desktop_ocr_agent.py --text 确定 --click
```

### 5.5 匹配模式

包含匹配，默认：

```bat
python desktop_ocr_agent.py --text 确定 --match contains
```

精确匹配：

```bat
python desktop_ocr_agent.py --text 确定 --match exact
```

正则匹配：

```bat
python desktop_ocr_agent.py --text "确.*" --match regex
```

---

## 6. OpenClaw 调用示例

### 6.1 扫描主屏

对 OpenClaw 说：

```text
调用 desktop_ocr_scan_primary 扫描主屏幕。
```

### 6.2 先 dry-run 查找“确定”

```text
调用 desktop_ocr_click_text，text=确定，match=contains，click=false。
```

### 6.3 确认后真实点击“确定”

```text
调用 desktop_ocr_click_text，text=确定，match=contains，click=true。
```

---

## 7. 配置说明

配置文件：

```text
config.json
```

关键配置：

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

建议保持：

```json
"dry_run": true
```

真实点击应通过 `--click` 或 OpenClaw 工具参数 `click=true` 临时开启。

---

## 8. 主屏限制说明

本插件只使用 Windows 主屏幕尺寸截图：

```text
bbox = (0, 0, 主屏宽度, 主屏高度)
```

当前实现通过 Windows `GetSystemMetrics(0/1)` 取得主屏大小，并用 `PIL.ImageGrab` 截图。

注意：如果 Windows 显示设置中把副屏设为“主显示器”，插件会操作那个被 Windows 标记为主显示器的屏幕。

---

## 9. 验收记录

已在本机完成以下验证：

```bat
npm run typecheck
python -m py_compile desktop_ocr_agent.py
python desktop_ocr_agent.py --scan
python desktop_ocr_agent.py --text OpenClaw --dry-run
```

验证结论：

- TypeScript 类型检查通过；
- Python 语法检查通过；
- 主屏 OCR 可识别中文和英文；
- `logs/latest_ocr_results.json` 能输出识别文字、置信度、box、center；
- `screenshots/latest_debug.png` 能生成 OCR 标注图；
- dry-run 能定位文字并输出将点击坐标；
- 默认不会真实点击。

---

## 10. 常见问题排查

### 10.1 第一次运行很慢

PaddleOCR 第一次运行会下载模型，属于正常情况。模型下载完成后，后续会使用缓存。

### 10.2 OCR 结果为空

检查：

1. 当前主屏是否有清晰文字；
2. 查看 `screenshots/latest_primary.png` 是否截到了正确屏幕；
3. 查看 `logs/run.log` 是否有 PaddleOCR 报错；
4. 降低 `config.json` 里的 `confidence_min`，例如从 `0.55` 改为 `0.45`。

### 10.3 中文输出在 cmd 里乱码

部分 Windows cmd 环境会显示乱码，但日志和 JSON 文件使用 UTF-8 保存，一般不影响功能。优先查看：

```text
logs/latest_ocr_results.json
logs/run.log
```

### 10.4 PaddleOCR / PaddlePaddle 报错

本机已验证版本：

```text
paddlepaddle==3.2.2
paddleocr==3.5.0
numpy==2.3.5
```

如果误升级后报错，重新执行：

```bat
python -m pip install --force-reinstall "paddlepaddle==3.2.2"
python -m pip install "numpy<2.4,>=1.24"
```

### 10.5 不小心要真实点击怎么办

默认安全策略是 dry-run。只有以下情况才会真实点击：

```bat
python desktop_ocr_agent.py --text 目标文字 --click
```

或 OpenClaw 工具参数：

```text
click=true
```

如果不传 `--click` / `click=true`，不会真实点击。

---

## 11. 后续维护建议

1. 保持默认 dry-run，不建议默认真实点击；
2. 升级 PaddleOCR / PaddlePaddle 前先单独测试 `--scan`；
3. 如果 OpenClaw 插件加载失败，先运行 `npm run typecheck`；
4. 如果 OCR 识别异常，优先查看：
   - `screenshots/latest_primary.png`
   - `screenshots/latest_debug.png`
   - `logs/latest_ocr_results.json`
   - `logs/run.log`
5. 真实点击前，先用同样文字执行 dry-run 确认坐标。

---

## 12. 快速接手步骤

```bat
cd /d C:\Users\besam\.openclaw\workspace\extensions\desktop-ocr-automation
install_plugin_deps.bat
npm run typecheck
python -m py_compile desktop_ocr_agent.py
python desktop_ocr_agent.py --scan
python desktop_ocr_agent.py --text OpenClaw --dry-run
```

如果以上都正常，插件即可交给 OpenClaw 使用。
