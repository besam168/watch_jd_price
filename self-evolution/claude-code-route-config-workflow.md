# Claude Code Route Config Workflow

> 用途：当需要给本机 Claude Code 切模型路由或接第三方 OpenAI / Anthropic 兼容供应方时，避免把 `根地址`、`/v1`、模型名和实际可用性搞混。

---

## 适用场景

当出现以下情况时，优先走这份 workflow：
- 要给 `claude` CLI 切到新的供应方
- 用户给了一个 OpenAI 兼容地址和模型名，要求“给 Claude Code 配上”
- 需要判断 Claude Code 该填根地址还是 `/v1`
- 改完配置后，想快速确认到底有没有真生效

一句话原则：

**Claude Code 配路由，不看“像不像对”，要看“改完能不能最小真测通过”。**

---

## 默认配置顺序（写死）

### 1. 先看 Claude Code 真实配置文件
默认检查：
- `C:\Users\besam\.claude\settings.json`

重点字段：
- `ANTHROPIC_API_KEY`
- `ANTHROPIC_BASE_URL`
- `ANTHROPIC_MODEL`
- `ANTHROPIC_DEFAULT_HAIKU_MODEL`
- `ANTHROPIC_DEFAULT_SONNET_MODEL`
- `ANTHROPIC_DEFAULT_OPUS_MODEL`
- `ANTHROPIC_REASONING_MODEL`

### 2. 默认优先写“根地址”，不要盲写 `/v1`
如果对接的是第三方兼容供应方，Claude Code 这边更稳的默认做法是：
- **优先写根地址**，例如：`http://fast.jnm.lol/`
- 不要想当然写成：`http://fast.jnm.lol/v1`

原因：
- Claude Code 往往会自己拼 Anthropic 风格路径
- 如果你把 `/v1` 也硬写进去，容易导致路径拼重、返回异常或表面可配但实际不可用

### 3. 模型族字段统一指向同一个目标模型
如果目标是统一切到一个模型，例如 `gpt-5.3-codex`，则默认同步改：
- `ANTHROPIC_DEFAULT_HAIKU_MODEL`
- `ANTHROPIC_DEFAULT_SONNET_MODEL`
- `ANTHROPIC_DEFAULT_OPUS_MODEL`
- `ANTHROPIC_MODEL`
- `ANTHROPIC_REASONING_MODEL`

避免只改了一个入口，结果不同模式下走不同模型。

### 4. 改完立刻做最小真测
默认测试命令：
- `claude -p "只输出：CLAUDE_ROUTE_OK"`

判定标准：
- 返回固定文本 = 路由至少最小可用
- 不返回 / 报错 / 卡死 = 配置还不能算完成

### 5. 真测通过后再对外下结论
只有拿到最小真测成功结果，才可以说：
- 已切成功
- 这条路由可用
- 当前 Claude Code 已走某模型 / 某供应方

---

## 推荐实操模板

### 用户给出：
- 地址：`http://fast.jnm.lol/v1`
- key：`...`
- model：`gpt-5.3-codex`

### Claude Code 侧默认落地为：
- `ANTHROPIC_BASE_URL = http://fast.jnm.lol/`
- 模型相关字段统一填 `gpt-5.3-codex`

### 然后立即执行：
- `claude -p "只输出：CLAUDE_ROUTE_OK"`

如果回 `CLAUDE_ROUTE_OK`，再认定配置完成。

---

## 常见坑

### 坑 1：把用户给的 `/v1` 直接照抄进 Claude Code
这在某些兼容供应方上可能会错。

默认处理：
- 先改成根地址测试
- 不要先入为主认为 `/v1` 一定正确

### 坑 2：只改 `ANTHROPIC_MODEL`，没改其它默认模型字段
后果：
- 某些模式还会走旧模型
- 排查时很混乱

默认处理：
- 统一改全套模型字段

### 坑 3：改完只看配置文件，不做真测
这会导致“看起来配好了，其实没通”。

默认处理：
- 改完马上跑最小真测

### 坑 4：把 Claude Code 的配置规律和 OpenClaw 的模型配置规律混为一谈
两边都可能是兼容接口，但拼路径和读取配置的逻辑不完全一样。

默认处理：
- Claude Code 问题优先查 `.claude/settings.json`
- OpenClaw 问题优先查 `openclaw status` + `openclaw config get ...`

---

## 最小检查表

- [ ] 已查看 `C:\Users\besam\.claude\settings.json`
- [ ] 已确认 base URL 是否该用根地址
- [ ] 已统一模型族字段
- [ ] 已执行 `claude -p` 最小真测
- [ ] 真测通过后才对外确认

---

## 一句话总结

**Claude Code 切路由时，默认先用根地址、统一全套模型字段、最后用 `claude -p` 做最小真测；没真测通过，就不算真的配好。**
