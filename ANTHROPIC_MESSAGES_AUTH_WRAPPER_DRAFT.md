# OpenClaw Claude `/v1/messages` auth wrapper 草案

更新时间：2026-04-18

## 目标
把 Claude `/v1/messages` 第一轮实现中最后一块还没钉死的工程点写实：

**如何兼容 `x-api-key`，同时尽量复用现有 Gateway HTTP auth / scope / body 读取逻辑。**

---

## 当前真实约束

现有通用 helper：
- `handleGatewayPostJsonEndpoint(req, res, opts)`

它的顺序是：
1. path 检查
2. method 检查
3. `authorizeGatewayHttpRequestOrReply(...)`
4. scope check
5. `readJsonBodyOrError(...)`

问题在于：
- Claude 客户端更可能发 `x-api-key`
- 现有入口更天然偏向 `Authorization: Bearer ...`

所以 Claude `/v1/messages` 第一轮若强行直接套 `handleGatewayPostJsonEndpoint(...)`，容易被 auth 入口假设卡住。

---

## 当前定版建议

### 不建议
- 直接重写整套 gateway auth
- 为 Claude 单独造一套完全不同的权限体系
- 在 handler 主体里到处塞 `x-api-key` 特判

### 建议
新增两个最小函数：

1. `authorizeAnthropicMessagesRequest(req, res, opts)`
2. `handleAnthropicPostJsonEndpoint(req, res, opts)`

也就是：
- auth 入口单独 shim
- 其余流程尽量沿用现有 helper 的结构

---

## 1. `getAnthropicApiKey(req)`

```ts
function getAnthropicApiKey(req) {
  const xApiKey = getHeader(req, "x-api-key")?.trim();
  if (xApiKey) return xApiKey;
  return getBearerToken(req);
}
```

### 说明
第一轮只兼容：
- `x-api-key`
- `Authorization: Bearer ...`

`anthropic-version` 先只允许存在，不做强校验。

---

## 2. `authorizeAnthropicMessagesRequest(...)`

### 设计原则
- 不绕开现有 gateway auth
- 不复制 scope / rate-limit / trusted proxy 判断
- 只做“把 `x-api-key` 转成现有 auth 能吃的形状”

### 接近实装版伪代码

```ts
async function authorizeAnthropicMessagesRequest(req, res, opts) {
  const apiKey = getAnthropicApiKey(req);
  if (!apiKey) {
    sendUnauthorized(res);
    return null;
  }

  const originalAuthorization = req.headers.authorization;
  try {
    req.headers.authorization = `Bearer ${apiKey}`;
    return await authorizeGatewayHttpRequestOrReply({
      req,
      res,
      auth: opts.auth,
      trustedProxies: opts.trustedProxies,
      allowRealIpFallback: opts.allowRealIpFallback,
      rateLimiter: opts.rateLimiter
    });
  } finally {
    if (originalAuthorization === void 0) delete req.headers.authorization;
    else req.headers.authorization = originalAuthorization;
  }
}
```

### 说明
这版虽然有“临时改 header 再还原”的味道，但第一轮非常务实：
- 改动小
- 易接现有 auth
- 不破坏下游 scope / operator 逻辑

后续若要更洁净，可再改成 request-like wrapper，而不是直接碰原 req。

---

## 3. `handleAnthropicPostJsonEndpoint(...)`

### 为什么要有它
因为 Claude 这条线如果直接套 `handleGatewayPostJsonEndpoint(...)`：
- auth 已经先执行了
- 中间没法优雅插入 `x-api-key -> Bearer` shim

所以最稳的做法是：
- 复制它的结构
- 只替换 auth 那一步

### 接近实装版伪代码

```ts
async function handleAnthropicPostJsonEndpoint(req, res, opts) {
  if (new URL(req.url ?? "/", `http://${req.headers.host || "localhost"}`).pathname !== opts.pathname) {
    return false;
  }

  if (req.method !== "POST") {
    sendMethodNotAllowed(res);
    return;
  }

  const requestAuth = await authorizeAnthropicMessagesRequest(req, res, opts);
  if (!requestAuth) return;

  if (opts.requiredOperatorMethod) {
    const requestedScopes =
      opts.resolveOperatorScopes?.(req, requestAuth) ??
      resolveTrustedHttpOperatorScopes(req, requestAuth);

    const scopeAuth = authorizeOperatorScopesForMethod(
      opts.requiredOperatorMethod,
      requestedScopes
    );

    if (!scopeAuth.allowed) {
      sendJson$1(res, 403, {
        ok: false,
        error: {
          type: "forbidden",
          message: `missing scope: ${scopeAuth.missingScope}`
        }
      });
      return;
    }
  }

  const body = await readJsonBodyOrError(req, res, opts.maxBodyBytes);
  if (body === void 0) return;

  return {
    body,
    requestAuth
  };
}
```

---

## 4. Claude handler 如何接它

`handleAnthropicMessagesHttpRequest(...)` 第一段建议长这样：

```ts
async function handleAnthropicMessagesHttpRequest(req, res, opts) {
  const handled = await handleAnthropicPostJsonEndpoint(req, res, {
    pathname: "/v1/messages",
    requiredOperatorMethod: "chat.send",
    resolveOperatorScopes: resolveOpenAiCompatibleHttpOperatorScopes,
    auth: opts.auth,
    trustedProxies: opts.trustedProxies,
    allowRealIpFallback: opts.allowRealIpFallback,
    rateLimiter: opts.rateLimiter,
    maxBodyBytes: opts.maxBodyBytes ?? opts.config?.maxBodyBytes ?? DEFAULT_ANTHROPIC_MESSAGES_BODY_BYTES
  });

  if (handled === false) return false;
  if (!handled) return true;

  const senderIsOwner = resolveOpenAiCompatibleHttpSenderIsOwner(req, handled.requestAuth);
  const body = handled.body;

  // 后面再接 model/session/prompt/runtime bridge/response mapper
}
```

---

## 5. 为什么这条路线值钱

它解决的不是“代码优不优雅”，而是一个真实的实现卡点：

### 若没有这层 auth wrapper
前面所有 `/v1/messages` handler / runtime bridge / response mapper 草案，最终都可能卡死在：
- Claude 客户端请求根本进不来
- 或 auth 行为与 OpenAI 入口不一致

### 有了这层 wrapper
`/v1/messages` 第一轮就具备完整闭环骨架：
1. path / method
2. Claude auth
3. scope check
4. body read
5. request -> prompt
6. runtime bridge
7. Claude response

---

## 6. 当前定版结论

Claude `/v1/messages` 第一轮最合理的 auth 路线已经明确：

- **不硬套** `handleGatewayPostJsonEndpoint(...)`
- **不重做** gateway auth
- **而是新增一个 Claude 版小 wrapper**：
  - `authorizeAnthropicMessagesRequest(...)`
  - `handleAnthropicPostJsonEndpoint(...)`

这一步补完后，整条 `/v1/messages` 第一轮实现链路就从“几段草案”收口成了“可直接开改的模块清单”。
