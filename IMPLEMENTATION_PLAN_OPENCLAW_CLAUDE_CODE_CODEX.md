# OpenClaw 适配 Claude Code / Codex CLI 实施蓝图

更新时间：2026-04-18

## 一句话结论

这不是“补一个泛 OpenAI 兼容接口”就算完成。
要明确拆成两条线：

- **Claude Code** → **Anthropic-compatible Messages adapter** → OpenClaw Runtime
- **Codex CLI** → **OpenAI Responses-compatible adapter** → OpenClaw Runtime

其中：
- **Codex CLI 方向不是从零开始**：本机 OpenClaw 文档已确认存在 `GET /v1/models`、`POST /v1/responses`、`POST /v1/chat/completions`。
- **Claude Code 方向目前不是现成入口**：至少公开文档里还没有 `POST /v1/messages` 兼容面，因此应视为新增适配层。

---

## 当前本机 OpenClaw 现状（已确认）

### 已有 HTTP 兼容面
本机 OpenClaw 文档已明确：
- `GET /v1/models`
- `GET /v1/models/{id}`
- `POST /v1/embeddings`
- `POST /v1/chat/completions`
- `POST /v1/responses`

来源：
- `docs/gateway/index.md`
- `docs/gateway/openai-http-api.md`
- `docs/gateway/openresponses-http-api.md`
- `docs/gateway/configuration-reference.md`

### 已确认的关键特性
#### Responses API
- 支持 `Authorization: Bearer <token>`
- 支持 `stream: true`
- SSE 事件文档已存在
- 错误体为 OpenAI 风格：
  ```json
  { "error": { "message": "...", "type": "invalid_request_error" } }
  ```
- 需要注意 `x-openclaw-agent-id` / agent-first model contract

#### Chat Completions API
- 文档明确为 OpenAI-compatible
- `/v1/models` 与 `/v1/responses` 跟随同一 HTTP 兼容面一起暴露
- 使用 gateway bearer auth

### 当前最大的已知缺口
- 暂未看到公开支持 **Anthropic Messages** 的：
  - `POST /v1/messages`
  - `anthropic-version`
  - `x-api-key`
  - Claude 风格流式事件
  - `tool_use` / `tool_result`

所以：
- **Codex 线 = 先验现有能力，再补 gap**
- **Claude 线 = 新增 adapter 为主**

---

## 目标架构

```text
Claude Code --> Anthropic Adapter --> OpenClaw Runtime
Codex CLI   --> OpenAI Adapter ----> OpenClaw Runtime
```

内部统一格式建议：

```json
{
  "model": "openclaw-agent",
  "messages": [],
  "tools": [],
  "stream": true,
  "protocol": "anthropic|openai-responses"
}
```

注意：
- 外部按协议拆开
- 内部按 OpenClaw runtime 统一
- 不要把协议分歧扩散到 runtime 深处

---

## 实施顺序（修正版）

### Phase 0：请求探测与兼容日志
目标：
先看真实请求形态，不靠猜。

必须记录：
- method
- path
- query
- auth type（bearer / x-api-key / none）
- headers 摘要（敏感值打码）
- model
- stream
- request schema 摘要
- status code
- latency
- chunk count
- finish reason
- error body

建议日志样式：

```txt
[REQ] POST /v1/messages model=openclaw-claude stream=true auth=x-api-key
[HDR] x-api-key=*** anthropic-version=2023-06-01
[RES] 200 in 582ms
```

```txt
[REQ] POST /v1/responses model=openclaw-codex stream=true auth=bearer
[HDR] authorization=Bearer ***
[RES] 200 in 712ms chunks=21 finish=completed
```

验收：
- 能清晰区分 Claude Code 与 Codex CLI 请求
- 出错时能看到诊断所需最小信息
- 能关联到 runtime 成败与 finish reason

---

### Phase 1A：先验 Codex CLI 最小闭环
目标：
不要先写太多代码，先确定 OpenClaw 当前 Responses 兼容面的真实 gap。

优先验证：
1. `GET /v1/models`
2. `POST /v1/responses`
3. `POST /v1/responses` + `stream: true`
4. 真机 `codex` 连接

最小 curl：

```bash
curl http://127.0.0.1:18789/v1/models \
  -H "Authorization: Bearer oc_test_key"
```

```bash
curl http://127.0.0.1:18789/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer oc_test_key" \
  -d '{
    "model": "openclaw/default",
    "input": "hello"
  }'
```

```bash
curl -N http://127.0.0.1:18789/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer oc_test_key" \
  -d '{
    "model": "openclaw/default",
    "stream": true,
    "input": "hello"
  }'
```

本阶段产物：
- Codex 当前可用度报告
- 真实 gap list：
  - 模型名问题？
  - SSE 事件问题？
  - 错误体问题？
  - tool schema 问题？

---

### Phase 1B：新增 Claude Code 最小兼容入口
目标：
增加 `POST /v1/messages`，先打通单轮文本对话。

路径：
- `POST /v1/messages`

认证必须支持：
- `x-api-key: <key>`
- `Authorization: Bearer <key>`

最小请求兼容：
- `messages[].content` 为 string
- `messages[].content` 为 content block array

最小响应兼容：

```json
{
  "id": "msg_123",
  "type": "message",
  "role": "assistant",
  "model": "openclaw-claude",
  "content": [
    { "type": "text", "text": "Hello!" }
  ],
  "stop_reason": "end_turn"
}
```

本阶段先不强求：
- 完整 beta 语义
- 完整 Claude streaming taxonomy
- 工具调用

先把最小文本闭环打通。

---

### Phase 2：流式支持
#### Claude
补 `/v1/messages` streaming：
- 不断流
- 事件结构稳定
- 最终 stop 正常
- Claude Code 不报 parse error

#### Codex
补 `/v1/responses` SSE 兼容增强：
- `data: {...}`
- `data: [DONE]`
- 无 malformed event / invalid chunk

---

### Phase 3：工具调用
#### Claude Code
支持：
- `tool_use`
- `tool_result`

#### Codex CLI
支持：
- function/tool schema
- tool result 回传
- 流式工具事件

---

### Phase 4：字段清洗与错误标准化
必须做：
- unsupported fields 过滤
- model name 严格透传
- 不支持字段显式报错
- stream event 标准化
- 错误体标准化

---

## 外部模型命名规则

建议固定暴露：
- Claude Code：`openclaw-claude`
- Codex CLI：`openclaw-codex`

内部可以映射到同一 runtime / 同一 agent。
但外部名字必须稳定，不能偷偷改名。

补充建议：
- 同时继续保留 OpenClaw 原生 agent-first ids：
  - `openclaw`
  - `openclaw/default`
  - `openclaw/<agentId>`
- 新兼容层对外再额外提供稳定别名：
  - `openclaw-claude`
  - `openclaw-codex`

---

## 错误处理要求

### Claude 入口
至少支持：
- 401 认证失败
- 400 请求非法
- 404 模型或路径不存在
- 500 内部错误

### Codex / OpenAI 入口
建议统一：

```json
{
  "error": {
    "message": "Model not found",
    "type": "invalid_request_error",
    "code": "model_not_found"
  }
}
```

常见码：
- 401
- 400
- 404
- 429
- 500

---

## 交付物清单

### 文档交付
- 支持的 endpoint 列表
- 支持的认证方式
- 客户端配置示例
- 已知限制
- curl 验证命令

### 代码交付
- 新增 Anthropic adapter
- OpenAI Responses gap 修补
- 路由注册
- 协议映射层
- 错误处理
- 探测日志

### 验证交付
- curl 返回样例
- Claude Code 真机结果
- Codex CLI 真机结果

---

## 当前阶段的明确 next steps

### 立即执行
1. 查 OpenClaw dist / 源码中是否已有隐藏的 `/v1/messages` 或 Anthropic adapter 雏形
2. 确认 `/v1/responses` 当前 SSE 事件是否足够贴近 Codex CLI
3. 确认 `/v1/models` 的返回结构是否需要额外别名模型 `openclaw-codex`
4. 明确日志层该加在网关 HTTP 哪一层

### 然后再做
5. 出 gap 分析
6. 定位具体改造文件
7. 进入第一轮最小代码改造

---

## 当前工程判断（定版）

- **不要把“已有 OpenAI 兼容”误判成“已兼容 Codex CLI + Claude Code”**
- **Codex CLI 先验现有能力再增强**
- **Claude Code 直接新增 `/v1/messages` adapter**
- **先最小闭环，再流式，再工具调用**

这版顺序最稳，也最符合 OpenClaw 当前真实底座。
