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

验收结果：
- Node 成功生成 `.pptx`
- `python -m markitdown _tmp/pptx-smoke-test.pptx` 成功读出文本

注意：
- 直接在 Node 脚本里 `require('pptxgenjs')` 时，优先使用工作区本地 `node_modules`
- 不要依赖全局 npm 安装供脚本 `require()` 自动发现

### 2) minimax-xlsx
已可用（以读取/分析流程为主）。

本机已具备依赖：
- Python：`pandas` `openpyxl`

真测文件：
- 生成脚本：`_tmp/xlsx-smoke-test.py`
- 输出文件：`_tmp/xlsx-smoke-test.xlsx`

验收结果：
- openpyxl 成功生成 `.xlsx`
- `skills/minimax-xlsx/scripts/xlsx_reader.py` 成功读取并输出分析报告

注意：
- 当前 `templates/minimal_xlsx` 直接打包出的测试文件与本机 `openpyxl` 读取兼容性不稳，曾报 `ChildSheet.name NoneType` 错误
- 因此当前最稳路线：
  1. 用 `openpyxl` 或现有 Excel 文件作为输入
  2. 再用 minimax-xlsx 自带脚本做读取、分析、结构化修改
- 公式单元格如果未经过 Excel/LibreOffice 重算，读取时可能显示空缓存值；这是正常现象，不代表文件损坏

## 推荐用法

### PPT 生成
- 让模型先产出结构化内容
- 再用本地 Node 脚本调用 `pptxgenjs` 生成 PPT
- 如需反读文本，用 `markitdown[pptx]`

### XLSX 处理
- 读表/分析：`skills/minimax-xlsx/scripts/xlsx_reader.py`
- 其他脚本可按需试：
  - `xlsx_add_column.py`
  - `xlsx_insert_row.py`
  - `xlsx_shift_rows.py`
  - `formula_check.py`

## 后续建议

如果继续增强，下一步优先：
1. 给 `pptx-generator` 包一层本地桥接脚本，统一输入 JSON -> 输出 PPTX
2. 给 `minimax-xlsx` 包一层本地桥接脚本，统一读写参数
3. 再决定是否接 `minimax-pdf`
