# Coding Office

Coding Office 是一个 OpenClaw Skill，用来把 OpenClaw 变成本地 Coding Agent 调度台。它定义 Claude CLI、Codex CLI、未来 Tanzo 的安全调用流程，并优先参考/适配 `openclaw-safe-agent-cli-mcp` 插件。

## 当前定位

第一阶段不重造完整 MCP Server，而是做清晰可落地的调度规范：

```text
OpenClaw
  -> Coding Office Skill
  -> openclaw-safe-agent-cli-mcp
  -> Claude CLI / Codex CLI
  -> 本地项目 review / validate / task
```

Tanzo 先预留，等确认有 CLI/API 后再接。

## 推荐依赖

安装 ClawHub 插件：

```bash
openclaw plugins install clawhub:openclaw-safe-agent-cli-mcp
openclaw plugins enable safe-agent-cli-mcp
openclaw plugins inspect safe-agent-cli-mcp --json
```

参考仓库：

```text
https://github.com/udaymanish6/openclaw-safe-agent-cli-mcp
```

该插件提供 Claude/Codex 两套 MCP 工具：

| Agent | 工具 |
|---|---|
| Claude | `claude_status`, `claude_config`, `claude_validate`, `claude_review`, `claude_task` |
| Codex | `codex_status`, `codex_config`, `codex_validate`, `codex_review`, `codex_task` |

## 文件结构

```text
coding-office/
  SKILL.md
  README.md
  OPENCLAW_CODING_OFFICE_SPEC.md
  HANDOFF_TEMPLATE.md
  PROJECT_HANDOFF.md
  config/
    coding-office.example.json
  schemas/
    task.schema.json
    result.schema.json
  examples/
    review-request.json
    validate-request.json
    task-dry-run-request.json
    task-execute-request.json
```

## 工作流

### 1. 只读审查 review

先看项目，不改文件。

```json
{
  "agent": "auto",
  "mode": "review",
  "cwd": "C:\\path\\to\\project",
  "prompt": "检查这个项目的结构和风险",
  "dryRun": true,
  "allowWrites": false
}
```

### 2. 预检查 validate

任何写入前先 validate，确认路径、权限、命令预览和策略。

```json
{
  "agent": "codex",
  "mode": "validate",
  "cwd": "C:\\path\\to\\project",
  "prompt": "准备修复测试失败，先验证是否允许执行",
  "dryRun": true,
  "allowWrites": false
}
```

### 3. 写入预演 task dry-run

要改文件时，先让 task 返回预演，不执行写入。

```json
{
  "agent": "codex",
  "mode": "task",
  "cwd": "C:\\path\\to\\project",
  "prompt": "修复 parser 单元测试失败",
  "dryRun": true,
  "allowWrites": false
}
```

### 4. 真执行 task execute

用户确认后才允许：

```json
{
  "agent": "codex",
  "mode": "task",
  "cwd": "C:\\path\\to\\project",
  "prompt": "修复 parser 单元测试失败，并运行最小测试",
  "dryRun": false,
  "allowWrites": true
}
```

## 安全规则

必须遵守：

1. `allowedRoots` 只放具体项目目录，不放整个用户目录。
2. 默认 `dryRun: true`。
3. 真写入必须同时满足 `dryRun: false` 和 `allowWrites: true`。
4. 不暴露通用 shell。
5. 不读取、不输出 secret、token、cookie、password。
6. 不做删除目录、格式化、关机、改注册表等破坏性操作。
7. 安装依赖、数据库迁移、大范围重构、长期后台服务必须二次确认。

## Agent 选择建议

| 任务 | 推荐 |
|---|---|
| 代码修 bug | Codex |
| 测试失败 | Codex |
| 架构审查 | Claude |
| 文档/交接 | Claude |
| 安全风险分析 | Claude + Codex review |
| 不确定 | 先 `agent=auto`，只做 review |

## 验收方式

本 Skill 完成的最低验收：

1. `SKILL.md` 能指导 OpenClaw 何时调用 Coding Agent。
2. `README.md` 能指导安装依赖插件和使用流程。
3. `OPENCLAW_CODING_OFFICE_SPEC.md` 定义输入输出、安全模型、工具映射。
4. `config/coding-office.example.json` 存在且 JSON 合法。
5. `schemas/*.json` 存在且 JSON 合法。
6. `examples/*.json` 存在且可作为调用样例。
7. `PROJECT_HANDOFF.md` 说明当前完成情况、风险、下一步。

## 重要文档

- `SKILL.md`：OpenClaw 行为规则。
- `OPENCLAW_CODING_OFFICE_SPEC.md`：技术规格。
- `HANDOFF_TEMPLATE.md`：通用交接模板。
- `PROJECT_HANDOFF.md`：本项目交接清单。
