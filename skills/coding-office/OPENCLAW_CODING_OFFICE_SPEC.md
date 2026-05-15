# OpenClaw Coding Office 规格

## 1. 目标

Coding Office 让 OpenClaw 能安全调度本地 Coding Agent，按固定流程完成项目审查、验证、修改、测试和交接。

第一阶段目标不是重写完整 MCP Server，而是把 Skill、配置、schema、示例和交接规范落地，并优先适配 `openclaw-safe-agent-cli-mcp`。

## 2. 系统架构

```text
OpenClaw
  -> Coding Office Skill
  -> openclaw-safe-agent-cli-mcp
  -> Claude CLI / Codex CLI
  -> allowedRoots 内本地项目
```

未来可扩展：

```text
OpenClaw
  -> openclaw-coding-office-mcp
  -> Claude CLI / Codex CLI / Tanzo CLI
```

## 3. 组件职责

| 组件 | 职责 |
|---|---|
| OpenClaw | 理解用户目标、调用 Skill、向用户确认风险、汇总结果 |
| Coding Office Skill | 定义调度流程、安全底线、agent 选择、交接格式 |
| safe-agent-cli-mcp | 包装 Claude/Codex CLI，提供 dry-run、allowedRoots、write gate |
| Claude CLI | 方案、架构、审查、文档、交接 |
| Codex CLI | 代码修复、测试、结构化执行 |
| Tanzo | 预留，确认 CLI/API 后接入 |

## 4. 工具映射

| Coding Office 抽象 | Claude 工具 | Codex 工具 | 说明 |
|---|---|---|---|
| status | `claude_status` | `codex_status` | 检查本地 CLI 是否可用 |
| config | `claude_config` | `codex_config` | 查看脱敏配置、CLI 路径、allowedRoots |
| validate | `claude_validate` | `codex_validate` | 只验证输入和策略，不执行任务 |
| review | `claude_review` | `codex_review` | 默认只读/ dry-run，用于审查 |
| task | `claude_task` | `codex_task` | 执行任务；真写入必须双开关 |

## 5. 调度流程

### 5.1 新项目首次接入

1. 确认项目根目录。
2. 确认该目录在 `allowedRoots` 中。
3. 调用 `*_status` 检查 CLI 可用性。
4. 调用 `*_config` 检查配置脱敏输出。
5. 先做 `review`，不要直接 task。

### 5.2 审查流程

```text
用户提出检查/分析需求
  -> 选择 Claude 或 Codex
  -> review dry-run
  -> review real run（如果插件策略允许且仍只读）
  -> 汇总发现、风险、下一步
```

### 5.3 修改流程

```text
用户提出修改需求
  -> validate dry-run
  -> task dry-run
  -> 展示预览和风险
  -> 用户确认
  -> task dryRun=false + allowWrites=true
  -> 运行最小验证
  -> 交接总结
```

### 5.4 高风险流程

若涉及删除、迁移、安装依赖、大范围重构、系统设置或 secret，必须暂停并请求用户确认。确认前只能输出计划和风险，不能执行。

## 6. 统一任务输入

Schema 文件：`schemas/task.schema.json`

字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `agent` | string | 是 | `auto`, `claude`, `codex`, `tanzo` |
| `mode` | string | 是 | `status`, `config`, `validate`, `review`, `task` |
| `cwd` | string | 是 | 项目根目录，必须在 `allowedRoots` 内 |
| `prompt` | string | 是 | 明确任务说明 |
| `dryRun` | boolean | 是 | 默认 true |
| `allowWrites` | boolean | 是 | 默认 false；写入时必须 true |
| `timeoutSeconds` | number | 否 | 建议 120-600 |
| `acceptanceCriteria` | string[] | 否 | 验收标准 |
| `riskLevel` | string | 否 | `low`, `medium`, `high` |

示例：

```json
{
  "agent": "codex",
  "mode": "task",
  "cwd": "C:\\Users\\besam\\.openclaw\\workspace\\asan-voice-v1",
  "prompt": "修复登录页测试失败，只改相关文件，并运行最小测试。",
  "dryRun": true,
  "allowWrites": false,
  "timeoutSeconds": 300,
  "acceptanceCriteria": [
    "相关测试通过",
    "不修改无关文件",
    "输出修改文件清单"
  ],
  "riskLevel": "medium"
}
```

## 7. 统一结果输出

Schema 文件：`schemas/result.schema.json`

字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `status` | string | `completed`, `failed`, `needs_confirmation`, `blocked`, `dry_run` |
| `summary` | string | 简短总结 |
| `agent` | string | 实际使用的 agent |
| `mode` | string | 实际模式 |
| `cwd` | string | 项目目录 |
| `changedFiles` | array | 修改文件 |
| `verification` | array | 验证命令和结果 |
| `risks` | array | 风险 |
| `nextSteps` | array | 下一步 |
| `handoffRequired` | boolean | 是否需要交接清单 |

## 8. 配置模型

配置示例：`config/coding-office.example.json`

核心配置：

- `allowedRoots`: 允许项目根目录。
- `defaultAgent`: 默认 agent。
- `defaultMode`: 默认模式，推荐 `review`。
- `requireValidateBeforeTask`: 写入前必须 validate。
- `requireDryRunBeforeExecute`: 真执行前必须 dry-run。
- `writeGate`: 写入双开关。
- `denyCommands`: 禁止命令片段。
- `redaction`: 输出脱敏规则。

## 9. 安全模型

### 9.1 必须有的控制

1. realpath 后检查 `cwd` 是否在 `allowedRoots` 内。
2. 默认 dry-run。
3. task 真执行必须 `dryRun=false` 且 `allowWrites=true`。
4. 不暴露通用 shell。
5. 命令预览必须可见。
6. 输出要尽量脱敏。
7. 用户确认前不执行高风险操作。

### 9.2 禁止操作

- 删除/清空目录。
- 格式化磁盘、关机、改注册表、改系统策略。
- 读取或输出密钥、token、cookie、password、SSH key。
- 访问 `allowedRoots` 外的项目。
- 未确认安装依赖、迁移数据库、启动长期服务。

### 9.3 风险分级

| 等级 | 例子 | 处理 |
|---|---|---|
| low | 只读审查、文档说明 | 可直接 review |
| medium | 小范围代码修改、跑测试 | validate + dry-run + 用户确认 |
| high | 删除、迁移、依赖大升级、多项目改动 | 暂停并二次确认，必要时拒绝 |

## 10. 错误码建议

| 错误码 | 含义 |
|---|---|
| `AGENT_NOT_AVAILABLE` | Claude/Codex/Tanzo 不可用 |
| `CWD_NOT_ALLOWED` | cwd 不在 allowedRoots 内 |
| `VALIDATION_REQUIRED` | task 前未 validate |
| `DRY_RUN_REQUIRED` | 真执行前未 dry-run |
| `WRITE_GATE_REQUIRED` | 缺少 `dryRun=false` 或 `allowWrites=true` |
| `DANGEROUS_OPERATION` | 命中禁止操作 |
| `SECRET_RISK` | prompt 或输出疑似包含 secret |
| `USER_CONFIRMATION_REQUIRED` | 需要用户确认 |
| `TIMEOUT` | 执行超时 |

## 11. Tanzo 接入预留

如果 Tanzo 后续提供 CLI/API，应实现同等工具：

- `tanzo_status`
- `tanzo_config`
- `tanzo_validate`
- `tanzo_review`
- `tanzo_task`

要求：

- 同样遵守 `allowedRoots`。
- 同样 dry-run first。
- 同样 write gate。
- 同样无通用 shell。
- 同样结构化输出和脱敏。

## 12. 验收标准

Coding Office 第一阶段完成标准：

1. OpenClaw 能通过 `SKILL.md` 明确知道何时调用 Coding Agent。
2. 用户能通过 `README.md` 安装参考插件、理解流程。
3. 规格文件定义工具映射、输入输出、安全模型、错误码。
4. 配置示例存在且 JSON 合法。
5. task/result schema 存在且 JSON 合法。
6. examples 目录提供 review、validate、task dry-run、task execute 示例。
7. 项目交接清单说明当前完成、未完成、风险、下一步和验收方法。
