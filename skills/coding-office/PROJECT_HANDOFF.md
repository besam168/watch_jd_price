# Coding Office 项目交接清单

## 1. 项目简介

- 项目名：Coding Office
- 项目路径：`C:\Users\besam\.openclaw\workspace\skills\coding-office`
- 项目目标：把 OpenClaw 变成本地 Coding Agent 调度台，安全调用 Claude CLI、Codex CLI，未来预留 Tanzo。
- 当前状态：第一阶段 Skill/文档/配置框架已完成，可作为 OpenClaw 调度规范使用。
- 适用范围：本地代码审查、验证、修改任务调度、项目交接。
- 不包含范围：暂不实现自研 MCP Server；暂不接阿三语音；暂不确认 Tanzo CLI/API。

## 2. 目录结构

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

- 关键目录：`config/`, `schemas/`, `examples/`
- 关键文件：`SKILL.md`, `README.md`, `OPENCLAW_CODING_OFFICE_SPEC.md`
- 入口文件：`SKILL.md`
- 配置文件：`config/coding-office.example.json`
- Schema 文件：`schemas/task.schema.json`, `schemas/result.schema.json`
- 交接模板：`HANDOFF_TEMPLATE.md`

## 3. 运行方式

### 3.1 安装参考插件

```bash
openclaw plugins install clawhub:openclaw-safe-agent-cli-mcp
openclaw plugins enable safe-agent-cli-mcp
openclaw plugins inspect safe-agent-cli-mcp --json
```

### 3.2 配置 allowedRoots

复制并调整：

```text
config/coding-office.example.json
```

只把具体项目目录放进 `allowedRoots`，不要放：

```text
C:\Users\besam
C:\
```

### 3.3 使用流程

1. 新项目先 `status/config`。
2. 默认先 `review`。
3. 需要修改时先 `validate`。
4. 再做 `task` dry-run。
5. 用户确认后才 `task` 真执行。
6. 真执行必须 `dryRun=false` 且 `allowWrites=true`。
7. 最后补交接清单和验证结果。

### 3.4 验证方式

在项目目录运行：

```bash
node -e "for (const f of ['config/coding-office.example.json','schemas/task.schema.json','schemas/result.schema.json','examples/review-request.json','examples/validate-request.json','examples/task-dry-run-request.json','examples/task-execute-request.json']) { JSON.parse(require('fs').readFileSync(f,'utf8')); console.log('OK', f); }"
```

## 4. 已完成内容

- 已补强 `SKILL.md`：明确触发条件、角色、safe-agent-cli-mcp 依赖、review/validate/task 流程、安全底线、agent 选择策略。
- 已补强 `README.md`：说明安装插件、目录结构、使用示例、验收方式。
- 已补强 `OPENCLAW_CODING_OFFICE_SPEC.md`：定义架构、工具映射、输入输出、配置模型、安全模型、错误码、Tanzo 预留、验收标准。
- 已补强 `HANDOFF_TEMPLATE.md`：增加运行方式、风险、调用记录、最终结论。
- 已新增 `config/coding-office.example.json`：包含 allowedRoots、agent 工具映射、策略、禁用命令、脱敏、handoff 配置。
- 已新增 `schemas/task.schema.json`：统一任务输入 schema。
- 已新增 `schemas/result.schema.json`：统一结果输出 schema。
- 已新增 `examples/*.json`：review、validate、task dry-run、task execute 调用样例。
- 已新增本文件 `PROJECT_HANDOFF.md`。

## 5. 当前真实验收状态（2026-05-15 更新）

### 5.1 已确认的关键事实

- **OpenClaw 当前系统内本来就已经暴露了原生 safe-agent CLI 工具**，可直接使用：
  - `safe-claude__claude_status`
  - `safe-claude__claude_config`
  - `safe-claude__claude_validate`
  - `safe-claude__claude_review`
  - `safe-claude__claude_task`
  - `safe-codex__codex_status`
  - `safe-codex__codex_config`
  - `safe-codex__codex_validate`
  - `safe-codex__codex_review`
  - `safe-codex__codex_task`
- 因此从实际使用角度，**系统原生就能直接调 Claude Code / Codex CLI**，并不一定非要依赖 `coding-agent` skill 去绕后台调度。
- `coding-agent` 更偏“后台 coding task 调度方式”；`safe-claude` / `safe-codex` 更偏“直接本地 CLI 工具接口”。

### 5.2 已做出的真实验收结果

- 本机直接命令验证：
  - `claude --version` 已成功返回 `2.1.119 (Claude Code)`
  - `codex --version` 已成功返回 `codex-cli 0.117.0`
- 原生 safe-* 工具的功能级 dry-run 验收：
  - `claude_validate`：通过
  - `codex_validate`：通过
  - `claude_review`（dryRun）：通过
  - `codex_review`（dryRun）：通过
  - `claude_task`（dryRun）：通过
  - `codex_task`（dryRun）：通过
- 上述结果说明：
  1. 命令拼装逻辑正常
  2. `allowedRoots` 白名单机制正常
  3. review 默认只读保护正常
  4. task 的 dry-run 与写入门禁逻辑正常

### 5.3 当前剩余边界

- 原生 safe-* 工具的 `status` / `config` 在当前会话里仍显示 Windows 下的 CLI 自动发现路径有些别扭：
  - 它们显示的 `claude` / `codex` 路径探测结果仍报 `ENOENT`
  - 但本机直接执行 `claude --version` / `codex --version` 实际是通的
- 因此当前最准确说法应为：
  - **系统原生 safe-agent 工具已可用于 validate / review / task 的 dry-run 流程**
  - **状态探测层仍有 Windows 路径发现的小问题**
  - 这不影响它作为“本地 CLI 安全包装器”的核心价值判断

## 6. 未完成内容

- 尚未真实安装/启用 `openclaw-safe-agent-cli-mcp`，需要在 OpenClaw 环境执行安装命令。
- 尚未确认 Claude CLI / Codex CLI 是否已安装并登录。
- 尚未把 `coding-office.example.json` 接到真实 OpenClaw 插件配置。
- 尚未实现自研 `openclaw-coding-office-mcp` 统一 server。
- Tanzo CLI/API 是否存在尚未确认，Tanzo 工具仍为预留。

## 6. 风险与注意事项

- 权限风险：`allowedRoots` 不能配置成整个用户目录或磁盘根目录。
- 写入风险：真实 task 必须经过 validate、dry-run、用户确认、`dryRun=false` + `allowWrites=true`。
- 数据风险：不要把 token、cookie、password、SSH key 放进 prompt 或输出。
- 配置风险：示例配置需要复制成真实本地配置后再改，不建议直接把示例当生产配置。
- 兼容性风险：safe-agent-cli-mcp、Claude CLI、Codex CLI 的参数可能随版本变化，需要用 `*_status` 和 `*_config` 验证。
- 安全边界：该方案降低风险，但不是 VM/容器/正式沙箱。

## 7. 下一步建议

1. 安装并启用 `openclaw-safe-agent-cli-mcp`。
2. 检查 Claude CLI / Codex CLI 是否可用：`claude_status`, `codex_status`。
3. 把具体项目目录加入 safe-agent-cli-mcp 的 `allowedRoots`。
4. 用 `examples/review-request.json` 做第一次只读 review。
5. 用 `examples/validate-request.json` 做写入前验证。
6. 只有确认安全后，再尝试 `task-dry-run-request.json`。
7. 最后再考虑真实 `task-execute-request.json`。

优先级：

1. 先跑通 Claude/Codex status/config。
2. 先跑通只读 review。
3. 再跑通 validate。
4. 最后跑通 task 写入。
5. 后续才做统一 MCP Server 和 Tanzo 接入。

## 8. 验收标准

本阶段算完成：

- 核心文档存在且内容完整。
- 配置示例、schema、example JSON 全部合法。
- OpenClaw 能根据 `SKILL.md` 知道何时调用 review/validate/task。
- 用户能根据 README 安装参考插件并理解安全流程。
- 项目交接清单能说明当前状态、风险、下一步。

本阶段不算完成：

- 直接声称已经接通 Claude/Codex 真实 CLI，但未安装验证。
- 允许无 `allowedRoots` 或默认写入。
- 允许跳过 validate/dry-run 直接 task。

复测方式：

1. 检查文件是否存在。
2. 运行 JSON parse 验证。
3. 安装插件后调用 `*_status`。
4. 使用 review 示例确认默认不写入。

## 9. Coding Office 调用记录

- 使用 agent：Tanzo 主执行，未调用外部 Claude/Codex。
- 使用模式：本地文件实现与文档落地。
- 是否 dry-run：不适用；本次由用户明确要求继续开工完成项目。
- 是否 allowWrites：用户已明确授权修改本项目文件。
- 验证命令：见第 3.4 节。
- 结果状态：待最终 JSON 验证后完成。

## 10. 最终交接结论

- 当前是否可继续开发：是。
- 当前是否可交付：第一阶段 Skill/文档框架可交付。
- 最大风险：尚未在真实 OpenClaw + safe-agent-cli-mcp + Claude/Codex CLI 环境中跑通端到端调用。
- 推荐下一步：安装插件，配置 allowedRoots，然后从只读 review 开始端到端测试。
