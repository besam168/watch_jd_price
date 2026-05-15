# Coding Office

Coding Office 是 OpenClaw 的本地 Coding Agent 调度 Skill。它不直接暴露 shell，而是把 Claude CLI、Codex CLI，以及未来 Tanzo CLI/API 当成本地“程序员”，按安全流程完成项目审查、验证、修改和交接。

## 1. 角色定位

- **OpenClaw**：总经理 / 调度员，负责理解用户目标、选择 agent、控制风险、汇总结果。
- **Coding Office Skill**：调度规则和交接规范，决定何时 review、validate、task。
- **openclaw-safe-agent-cli-mcp**：第一阶段推荐底层执行器，安全包装 Claude CLI / Codex CLI。
- **Claude CLI**：适合解释、方案、文档、复杂审查、风险评估。
- **Codex CLI**：适合代码修复、测试验证、结构化执行。
- **Tanzo**：预留第三程序员；确认有 CLI/API 后再接入。

第一阶段目标：**OpenClaw → Coding Office Skill → safe-agent-cli-mcp → Claude/Codex CLI**。

## 2. 触发条件

当用户要求以下事情时启用本 Skill：

- 检查一个项目、代码库、bug、报错或测试失败。
- 让 Claude/Codex/Tanzo 参与本地开发工作。
- 需要按“审查 → 验证 → 修改 → 测试 → 交接”流程推进。
- 需要生成项目交接清单、handoff、验收清单。

不需要启用本 Skill 的场景：

- 普通知识问答。
- 不涉及本地项目的聊天。
- 用户明确只要人工解释，不需要 agent 调度。

## 3. 推荐依赖插件

优先安装并使用 ClawHub 插件：

```bash
openclaw plugins install clawhub:openclaw-safe-agent-cli-mcp
openclaw plugins enable safe-agent-cli-mcp
openclaw plugins inspect safe-agent-cli-mcp --json
```

插件仓库：`https://github.com/udaymanish6/openclaw-safe-agent-cli-mcp`

该插件提供：

- `claude_status`, `claude_config`, `claude_validate`, `claude_review`, `claude_task`
- `codex_status`, `codex_config`, `codex_validate`, `codex_review`, `codex_task`

## 4. 固定工作流

### 4.1 status/config

新项目或首次使用时，先检查本地 agent 可用性：

1. `claude_status` / `codex_status`
2. `claude_config` / `codex_config`
3. 检查 `allowedRoots` 是否只包含具体项目目录。

### 4.2 review：先审查，不写入

用于读项目、分析 bug、看风险、给方案。

默认参数：

```json
{
  "cwd": "<project-root>",
  "prompt": "审查目标和问题说明",
  "dryRun": true
}
```

可用工具：

- `codex_review`：优先用于代码结构、测试、错误定位。
- `claude_review`：优先用于架构、文档、风险、交接分析。

### 4.3 validate：改动前预检查

任何写入前必须先 validate：

```json
{
  "cwd": "<project-root>",
  "prompt": "准备执行的任务说明",
  "dryRun": true,
  "timeoutSeconds": 120
}
```

validate 只检查输入、路径、策略、命令预览，不应实际修改文件。

### 4.4 task dry-run：写入前预演

需要修改代码时，先调用 task 的 dry-run：

```json
{
  "cwd": "<project-root>",
  "prompt": "明确、可验收的修改任务",
  "dryRun": true,
  "allowWrites": false
}
```

把 command preview、风险、计划展示给用户。

### 4.5 task execute：用户确认后才真执行

真执行必须同时满足：

```json
{
  "dryRun": false,
  "allowWrites": true
}
```

且必须满足全部条件：

1. `cwd` 在 `allowedRoots` 内。
2. 用户明确允许写入。
3. 任务范围具体、可回滚、可验证。
4. 不触发禁止事项。
5. 有最小验证命令或验收方法。

## 5. Agent 选择策略

`agent=auto` 时按下面规则选：

| 场景 | 首选 | 备选 |
|---|---|---|
| 代码 bug 修复 | Codex | Claude |
| 测试失败定位 | Codex | Claude |
| 架构审查 | Claude | Codex |
| 文档/交接 | Claude | Codex |
| 安全风险审查 | Claude | Codex |
| 大范围重构 | 先 Claude review | Codex task |
| 本地 Tanzo 专属任务 | Tanzo，若可用 | Codex |

不要为了“多 agent”而并行调用。只有在任务可拆分、互不写同一批文件时，才允许并行审查。

## 6. 安全底线

### 6.1 allowedRoots

只允许具体项目目录，不允许整个用户目录。

推荐：

```json
{
  "allowedRoots": [
    "C:\\Users\\besam\\.openclaw\\workspace\\skills\\coding-office",
    "C:\\Users\\besam\\.openclaw\\workspace\\asan-voice-v1"
  ]
}
```

禁止：

```json
{
  "allowedRoots": [
    "C:\\Users\\besam",
    "C:\\"
  ]
}
```

### 6.2 禁止事项

不得调用 Coding Agent 做以下事情：

- 删除或清空目录：`del /s`, `rmdir /s`, `Remove-Item -Recurse`, `rm -rf`。
- 格式化磁盘、关机、改注册表、改系统策略。
- 读取、输出、上传 secret、token、cookie、password、SSH key。
- 绕过 `allowedRoots`、软链接逃逸、访问无关项目。
- 未确认就安装依赖、升级大版本、迁移数据库。
- 未确认就启动长期后台服务。
- 未确认就进行大范围重构或批量改名。

### 6.3 高风险任务处理

发现高风险时必须先停下并向用户确认，说明：

- 为什么高风险。
- 会影响哪些文件/数据。
- 是否有备份或回滚方案。
- 建议的低风险替代方案。

## 7. 统一任务输入

Coding Office 自身推荐统一抽象：

```json
{
  "agent": "auto",
  "mode": "review",
  "cwd": "C:\\path\\to\\project",
  "prompt": "任务说明",
  "dryRun": true,
  "allowWrites": false,
  "timeoutSeconds": 120,
  "acceptanceCriteria": [
    "检查完成并返回风险",
    "不修改文件"
  ]
}
```

`mode` 只能是：`status`, `config`, `validate`, `review`, `task`。

## 8. 统一结果输出

每次 Coding Agent 完成后，OpenClaw 必须用下面格式回报：

```md
## 状态
完成 / 失败 / 需要确认

## 做了什么
- ...

## 修改文件
- 无 / path:line

## 验证
- 命令：...
- 结果：...

## 风险
- ...

## 下一步
- ...
```

## 9. 项目交接要求

每个被 Coding Office 接手的项目，最后必须能生成交接清单，至少包含：

1. 项目简介
2. 目录结构
3. 运行方式
4. 已完成内容
5. 未完成内容
6. 风险与注意事项
7. 下一步建议
8. 验收标准

模板见 `HANDOFF_TEMPLATE.md`。

## 10. Tanzo 预留

当前不假设 Tanzo 已有 CLI/API。确认后再新增：

- `tanzo_status`
- `tanzo_config`
- `tanzo_validate`
- `tanzo_review`
- `tanzo_task`

Tanzo 接入也必须遵守同样规则：allowedRoots、dry-run first、write gate、无通用 shell、输出脱敏。

## 11. 当前落地文件

本 Skill 至少包含：

- `SKILL.md`：OpenClaw 调度规则。
- `README.md`：安装、使用、验收说明。
- `OPENCLAW_CODING_OFFICE_SPEC.md`：接口、安全模型、流程规格。
- `HANDOFF_TEMPLATE.md`：通用项目交接模板。
- `config/coding-office.example.json`：安全配置示例。
- `schemas/task.schema.json`：任务输入 schema。
- `schemas/result.schema.json`：结果输出 schema。
- `examples/*.json`：review / validate / task 示例。
- `PROJECT_HANDOFF.md`：本项目当前交接清单。
