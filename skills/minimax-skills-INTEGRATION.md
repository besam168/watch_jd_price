# MiniMax Skills 本机接入说明（当前已接通）

更新时间：2026-04-26

已接入技能：
- `skills/pptx-generator`
- `skills/minimax-xlsx`

## 当前状态

### 1) pptx-generator
已可用。

本机已补齐依赖：
- 本地 npm 包：`pptxgenjs` `react-icons` `react` `react-dom` `sharp`
- Python：`markitdown[pptx]`

真测文件：
- 生成脚本：`_tmp/pptx-smoke-test.js`
- 输出文件：`_tmp/pptx-smoke-test.pptx`
- JSON 桥接示例：`_tmp/pptx-bridge-demo.json`
- JSON 桥接输出：`_tmp/pptx-bridge-demo.pptx`
- Markdown 桥接示例：`_tmp/pptx-bridge-demo.md`
- Markdown 桥接输出：`_tmp/pptx-bridge-from-md.pptx`

桥接脚本：
- `skills/pptx-generator/scripts/make-pptx.js`
- `skills/pptx-generator/scripts/make-pptx.ps1`

用法：
```powershell
powershell -ExecutionPolicy Bypass -File skills/pptx-generator/scripts/make-pptx.ps1 \
  -InputJson _tmp/pptx-bridge-demo.json \
  -OutputPptx _tmp/pptx-bridge-demo.pptx
```

也支持 Markdown / 中文提纲：
```powershell
powershell -ExecutionPolicy Bypass -File skills/pptx-generator/scripts/make-pptx.ps1 \
  -InputJson _tmp/pptx-bridge-demo.md \
  -OutputPptx _tmp/pptx-bridge-from-md.pptx
```

Markdown 约定：
- `#`：整份标题（首次出现）
- `##`：新页面标题
- `-` / `*`：项目符号
- 普通文本：页面正文

验收结果：
- Node 成功生成 `.pptx`
- `python -m markitdown ...pptx` 成功读出文本
- Markdown/中文提纲 -> PPT 链路已打通

注意：
- 直接在 Node 脚本里 `require('pptxgenjs')` 时，优先使用工作区本地 `node_modules`
- 不要依赖全局 npm 安装供脚本 `require()` 自动发现
- 当前反读中文时终端编码显示可能乱码，但不影响 PPT 文件本身生成

### 2) minimax-xlsx
已可用（当前桥接支持创建 / 分析 / 更新单元格）。

本机已具备依赖：
- Python：`pandas` `openpyxl`

真测文件：
- 生成脚本：`_tmp/xlsx-smoke-test.py`
- 输出文件：`_tmp/xlsx-smoke-test.xlsx`
- 桥接示例：`_tmp/xlsx-bridge-demo.json`
- 桥接输出：`_tmp/xlsx-bridge-demo.xlsx`
- 更新 spec：`_tmp/xlsx-update-demo.json`
- 更新输出：`_tmp/xlsx-bridge-updated.xlsx`

桥接脚本：
- `skills/minimax-xlsx/scripts/bridge.py`
- `skills/minimax-xlsx/scripts/bridge.ps1`

推荐当前直接用法（最稳）：
```powershell
python skills/minimax-xlsx/scripts/bridge.py create --input _tmp/xlsx-bridge-demo.json --output _tmp/xlsx-bridge-demo.xlsx
python skills/minimax-xlsx/scripts/bridge.py analyze --input _tmp/xlsx-bridge-demo.xlsx
python skills/minimax-xlsx/scripts/bridge.py update-cells --input _tmp/xlsx-bridge-demo.xlsx --spec _tmp/xlsx-update-demo.json --output _tmp/xlsx-bridge-updated.xlsx
```

更新 spec 结构：
```json
{
  "updates": [
    {"sheet": "Summary", "cell": "B2", "value": 18},
    {"sheet": "Summary", "cell": "C2", "value": "updated"}
  ]
}
```

PowerShell 包装脚本已创建，但当前在参数透传上不如直接调 Python 稳，后续再修。

验收结果：
- openpyxl 成功生成 `.xlsx`
- bridge.py 成功输出工作簿摘要 JSON
- `update-cells` 已成功修改并另存文件
- `skills/minimax-xlsx/scripts/xlsx_reader.py` 也已成功读取 smoke test 文件

注意：
- 当前 `templates/minimal_xlsx` 直接打包出的测试文件与本机 `openpyxl` 读取兼容性不稳，曾报 `ChildSheet.name NoneType` 错误
- 因此当前最稳路线：
  1. 用 `openpyxl` 或现有 Excel 文件作为输入
  2. 再用 minimax-xlsx 自带脚本做读取、分析、结构化修改
- 公式单元格如果未经过 Excel/LibreOffice 重算，读取时可能显示空缓存值；这是正常现象，不代表文件损坏

## 后续建议

如果继续增强，下一步优先：
1. 给 `minimax-xlsx` 的 PowerShell 包装层修好参数透传
2. 给 PPT 增加模板 / 母版 / 图片占位能力
3. 给 XLSX 增加 append-sheet / append-rows 动作
4. 再决定是否接 `minimax-pdf`
