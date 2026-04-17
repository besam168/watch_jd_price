# OpenClaw Claude Code / Codex CLI Gap 分析

更新时间：2026-04-18

## 结论先行

当前本机 OpenClaw（2026.4.2）已经具备较完整的 **OpenAI-compatible HTTP surface**，但**尚未看到公开的 Anthropic Messages 兼容入口**。

因此：
- **Codex CLI 方向 = 现有能力验证 + 小幅增强**
- **Claude Code 方向 = 新增 `/v1/messages` adapter**

---

## 已确认存在的能力

### 1. `/v1/models`
在 `gateway-cli-*.js` 中已定位到：
- `handleOpenAiModelsHttpRequest`
- `loadAgentModelIds`
- `toOpenAiModel`

已知行为：
- 返回的是 **agent-first model ids**，不是原始 provider model ids
- 默认包含：
  - `openclaw`
  - `openclaw/default`
  - `openclaw/<agentId>`

### 2. `/v1/responses`
已定位到：
- `handleOpenResponsesHttpRequest`
- `CreateResponseBodySchema`
- `writeSseEvent`
- `runResponsesAgentCommand`

已知行为：
- 走 OpenResponses 风格
- Bearer auth
- SSE 已有实现
- 工具相关字段已出现：
  - `extractClientTools`
  - `applyToolChoice`
  - `createFunctionCallOutputItem`

### 3. `/v1/chat/completions`
已定位到 OpenAI chat 兼容实现所在区段。
说明 OpenClaw 当前的 OpenAI 兼容面不是空壳，而是明确成体系存在。

---

## 已确认缺口

### A. 没看到 `/v1/messages`
截至当前勘探：
- 没有定位到 `POST /v1/messages` HTTP handler
- 没看到公开 `anthropic-version` 兼容入口
- 没看到 `x-api-key` 作为 Anthropic auth surface 的明确实现

这意味着 Claude Code 所需的 Anthropic Messages 面，当前不能默认视为已存在。

### B. 模型命名对 Codex CLI 未必最友好
当前 `/v1/models` 返回 agent-first ids：
- `openclaw`
- `openclaw/default`
- `openclaw/<agentId>`

但你的任务单想暴露稳定别名：
- `openclaw-codex`
- `openclaw-claude`

这不是必须推翻现有设计，但大概率需要在兼容层额外加 alias。

### C. Claude / Codex 需要两套不同协议语义
虽然 OpenClaw 已有 OpenAI 面：
- 这不等于已兼容 Claude Messages
- 也不等于已完全兼容 Codex CLI 的 parser / stream / tool-calling 习惯

所以不能拿“已有 `/v1/responses`”直接宣称双 CLI 全兼容。

---

## 现阶段最可能的改造落点

## 1. Gateway HTTP 路由注册层
目标：
- 在现有 gateway HTTP handler 分发逻辑中，新增 `/v1/messages`
- 挂接统一 auth / logging / operator scope 检查

## 2. OpenAI 兼容层模型枚举逻辑
目标：
- 在 `loadAgentModelIds()` / `toOpenAiModel()` 附近扩展可选 alias
- 或单独给兼容层写 stable model alias resolver

建议：
- 不要破坏原有 `openclaw/default`
- 新增兼容别名，而不是替换原语义

## 3. Responses SSE / tool-calling 映射层
目标：
- 用真机 Codex CLI 验证当前 SSE 事件是否已足够
- 若不够，再补 event 结构与 tool item 兼容

## 4. 新增 Anthropic Messages adapter 文件
目标：
- 独立实现：
  - request schema
  - auth 兼容
  - runtime request mapping
  - Claude response mapping
  - 后续 streaming mapping

建议：
- 不要硬塞进现有 OpenAI handler
- 用独立模块保持边界清晰

---

## 推荐的代码改造顺序

### 第一轮
- 加请求探测日志
- 验 `/v1/models`
- 验 `/v1/responses`
- 记录 Codex gap

### 第二轮
- 新增 `/v1/messages` 最小非流式版本
- 支持 `x-api-key` / Bearer
- 支持 string content / content blocks

### 第三轮
- Claude streaming
- Codex SSE 兼容增强

### 第四轮
- 双边 tools
- 字段清洗
- 错误标准化

---

## 现在就能定下来的工程判断

1. **OpenClaw 已有 OpenAI 兼容底座**，尤其是 `/v1/models` 与 `/v1/responses`
2. **Claude Code 兼容不能靠现有 OpenAI 面冒充**
3. **最值钱的第一步不是盲改，而是先拿 Codex 做真实 gap 验证**
4. **真正新增开发的主任务，是 `/v1/messages` Anthropic adapter**

---

## 下一步建议

立即进入：
1. 精确定位网关 HTTP 路由分发代码块
2. 增加 `/v1/messages` 的最小 handler 设计
3. 写第一版 curl 验证清单
4. 进入代码级实施
