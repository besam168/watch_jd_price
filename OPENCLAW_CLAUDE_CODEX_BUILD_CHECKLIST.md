# OpenClaw Claude/Codex 兼容改造施工清单（第一轮）

更新时间：2026-04-18

## 目标
把当前“方向判断 + 缺口分析”进一步压成**可直接动手的施工点**。

---

## 0. 已确认的源码锚点（避免下次重翻）

### Gateway 主 HTTP 分发
文件：
- `C:\Users\besam\AppData\Roaming\npm\node_modules\openclaw\dist\gateway-cli-CWpalJNJ.js`

当前已定位到的关键锚点：
- `createGatewayHttpServer(opts)`：约 `24272`
- `requestStages` 中 `models` stage：约 `24306`
- `openresponses` stage：约 `24354`
- `openai` stage：约 `24364`

结论：
- 如果要插入新的 `anthropic-messages` stage，当前最自然的位置就是 `models/embeddings` 之后、`openresponses/openai` 前后这一段。

### OpenAI 兼容现有 handler
同文件已定位：
- `resolveRequestPath(req)`：约 `21522`
- `handleOpenAiModelsHttpRequest(req, res, opts)`：约 `21525`
- `handleOpenAiHttpRequest(req, res, opts)`：约 `21846`
- `handleOpenResponsesHttpRequest(req, res, opts)`：约 `22547`

### Gateway 启用开关汇总
同文件已定位：
- `openAiChatCompletionsEnabled` 汇总：约 `24760`
- `openResponsesEnabled` 汇总：约 `24762`
- `createGatewayHttpServer(...)` 实际注入参数：约 `25459` 起

### 配置类型锚点
文件：
- `C:\Users\besam\AppData\Roaming\npm\node_modules\openclaw\dist\plugin-sdk\src\config\types.gateway.d.ts`

已定位：
- `GatewayHttpEndpointsConfig`：约 `308`
- `GatewayHttpConfig`：约 `321`

结论：
- 新增 `messages` endpoint config，优先就在这两处附近扩。

---

## A. 网关 HTTP 路由分发层

### 已定位
文件（dist 产物）：
- `C:\Users\besam\AppData\Roaming\npm\node_modules\openclaw\dist\gateway-cli-CWpalJNJ.js`

关键函数：
- `createGatewayHttpServer(opts)`

关键区块：
- `handleRequest(req, res)`
- `requestStages = [...]`

### 第一轮要做
1. 在 `requestStages` 中新增 stage：
   - `anthropic-messages`
2. 调用新 handler：
   - `handleAnthropicMessagesHttpRequest(req, res, opts)`
3. 建议放置位置：
   - `models / embeddings` 后
   - `openresponses / openai` 前后附近
   - 保持兼容类 HTTP 入口集中

---

## B. 配置类型层

### 已定位
文件：
- `C:\Users\besam\AppData\Roaming\npm\node_modules\openclaw\dist\plugin-sdk\src\config\types.gateway.d.ts`

已存在：
- `GatewayHttpChatCompletionsConfig`
- `GatewayHttpResponsesConfig`
- `GatewayHttpEndpointsConfig`
- `GatewayHttpConfig`

### 第一轮要做
新增：
- `GatewayHttpMessagesConfig`

并接入：
- `GatewayHttpEndpointsConfig.messages?: GatewayHttpMessagesConfig`

第一版最小字段：
```ts
export type GatewayHttpMessagesConfig = {
  enabled?: boolean;
  maxBodyBytes?: number;
};
```

后续再扩流式/工具开关。

---

## C. `/v1/messages` handler 层

### 现状
尚未看到公开现成 handler。

### 第一轮要新建/新增
建议函数：
- `handleAnthropicMessagesHttpRequest(req, res, opts)`
- `authorizeAnthropicMessagesRequest(req, res, opts)`
- `createClaudeMessageResponse(params)`
- `extractTextFromClaudeContent(content)`
- `buildClaudeMessagesPrompt(body)`

### 最小职责拆分
#### 1. path / method
- 仅接 `POST /v1/messages`
- 非 POST → `405`

#### 2. auth
兼容：
- `x-api-key`
- `Authorization: Bearer`

建议策略：
- 最终仍走 gateway token/password 校验
- `x-api-key` 可在进入通用 auth 前映射为 bearer 语义或单独 shim

#### 3. schema
最小支持：
- `model`
- `max_tokens`
- `messages`
- `system?`
- `stream?`

#### 4. runtime 映射
复用现有 ingress：
- `resolveGatewayRequestContext(...)`
- `agentCommandFromIngress(...)`

#### 5. response 映射
输出 Claude Messages 风格 JSON

---

## D. 模型别名层

### 已定位
关键函数：
- `loadAgentModelIds()`
- `toOpenAiModel(id)`
- `resolveAgentIdFromModel(model)`

### 当前现状
当前返回：
- `openclaw`
- `openclaw/default`
- `openclaw/<agentId>`

### 第一轮建议
先**不要破坏原有 agent-first contract**。

新增兼容别名策略：
- `openclaw-codex`
- `openclaw-claude`

可以有两种做法：
1. 直接扩 `loadAgentModelIds()`
2. 单独在兼容层做 alias resolver / alias list

第一轮更稳建议：
- **先在兼容层单独做 alias**，别直接污染原 agent-first 基础语义

---

## E. Codex CLI 验证层

### 已定位
关键 handler：
- `handleOpenAiModelsHttpRequest(...)`
- `handleOpenResponsesHttpRequest(...)`

### 第一轮要做
不是立刻大改，而是先补真实验证清单：
1. `GET /v1/models`
2. `POST /v1/responses`
3. `POST /v1/responses` with `stream: true`
4. 真机 `codex` provider 接入

### 验证重点
- model id 是否被 Codex 接受
- SSE event 是否被 Codex parser 接受
- tool schema 是否要后补
- 错误体是否够标准

---

## F. 日志层

### 现状
目前已有各 handler 的错误日志，但没有专门面向“协议兼容诊断”的统一摘要日志。

### 第一轮建议新增
统一兼容日志字段：
- protocol (`anthropic-messages` / `openai-responses` / `openai-chat`)
- path
- auth type
- model
- stream
- status
- latency
- chunk count
- finish reason

这层可以：
- 先做轻量日志
- 不必一上来搞复杂 tracing

---

## G. 推荐第一轮真实开发顺序

### Step 1
补配置类型：
- `messages.enabled`
- `messages.maxBodyBytes`

### Step 2
新增 `/v1/messages` 非流式 handler
- 只支持文本
- 只支持最小 schema
- 先返回 Claude 风格 JSON

### Step 3
接入总路由 `requestStages`

### Step 4
写 curl 验证
- `x-api-key`
- Bearer
- string content
- block content

### Step 5
回头做 Codex 真 gap 验证
- 不盲改 `/v1/responses`
- 先实测再补

---

## 当前最适合的执行方式

如果马上进入编码：
- **我负责总控 + 设计 + 验收口径**
- 执行层可以直接按这份清单逐点实施

如果继续手工本机勘探：
- 下一步优先抓 `handleOpenAiHttpRequest(...)` 周边，参考它的 handler 组织方式来搭 `/v1/messages`

---

## 当前定版结论

第一轮最值钱的改造，不是乱动 `/v1/responses`，而是：

1. **给 OpenClaw 增一个最小可用的 `/v1/messages`**
2. **保留现有 `/v1/models` + `/v1/responses` 作为 Codex 基线**
3. **用真实 curl / CLI 验证来决定 Codex 还缺什么**
