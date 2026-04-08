# OpenClaw 另一台电脑修复“放行条 / 审批条”通用教程（可直接复制）

> 用途：把这份教程复制到另一台电脑上，按步骤操作，修复 OpenClaw Control UI / WebChat 中执行命令时频繁弹出的“放行条 / 审批条”。

---

## 一、适用现象

如果你在另一台电脑上遇到下面情况，这份教程就适用：

- 执行本机命令时频繁弹出批准条
- `openclaw status`、`git status`、`npm -v` 这类简单命令也会要求放行
- 工作经常被 exec 审批打断

---

## 二、修复思路（先理解一句话）

要真正关掉放行条，必须同时处理两层：

### 第 1 层：请求侧配置
也就是 OpenClaw 的：

- `tools.exec.host`
- `tools.exec.security`
- `tools.exec.ask`

### 第 2 层：Gateway 审批策略
也就是 gateway 主机上的 approvals 配置：

- `defaults.security`
- `defaults.ask`
- `defaults.askFallback`

> 只改其中一层，通常不够。

---

## 三、直接可复制的修复步骤

### 步骤 1：先把 gateway approvals 改掉

运行：

```bash
openclaw approvals set --gateway --stdin
```

然后粘贴下面这段 JSON：

```json
{
  "version": 1,
  "defaults": {
    "security": "full",
    "ask": "off",
    "askFallback": "full"
  }
}
```

按保存/提交结束。

---

### 步骤 2：把请求侧 exec 配置改掉

依次运行：

```bash
openclaw config set tools.exec.host gateway
openclaw config set tools.exec.security full
openclaw config set tools.exec.ask off
```

---

### 步骤 3：重启 gateway

运行：

```bash
openclaw gateway restart
```

> 这一条不要省。很多“明明改了还弹条”的问题，最后就是没重启 gateway。

---

## 四、修完后立刻验证

### 1）检查 gateway approvals

运行：

```bash
openclaw approvals get --gateway
```

你应该看到类似：

- `security=full`
- `ask=off`
- `askFallback=full`

---

### 2）检查请求侧配置

运行：

```bash
openclaw config get tools.exec.host
openclaw config get tools.exec.security
openclaw config get tools.exec.ask
```

理想输出应是：

```text
gateway
full
off
```

---

### 3）做最小测试

运行下面几条：

```bash
openclaw status
```

```bash
git status
```

```bash
node -e "console.log('NODE_OK')"
```

```bash
npm -v
```

如果这些命令都能直接执行、不弹放行条，说明主路径已经修好了。

---

## 五、如果修完后还是弹条，怎么判断是哪一类问题

### 情况 A：配置根本没生效
先重新检查：

```bash
openclaw approvals get --gateway
openclaw config get tools.exec.host
openclaw config get tools.exec.security
openclaw config get tools.exec.ask
```

如果不是：

- host = `gateway`
- security = `full`
- ask = `off`

那就是配置没配对。

---

### 情况 B：配置改了，但 gateway 没真正吃到新配置
重跑：

```bash
openclaw gateway restart
```

然后再做验证。

---

### 情况 C：普通命令不弹，但复杂命令偶发弹
如果下面这些都不弹：

- `openclaw status`
- `git status`
- `node -e ...`
- `npm -v`

但某些复杂场景会弹，说明更像：

- 某条命令走了特殊路径
- 某种执行方式命中了不同分支
- 前端残留了旧的审批 UI
- 不是全局配置失效

这时候不要立刻推翻修复结果。

---

## 六、建议的排查顺序（复制到另一台电脑也适用）

### 第一步：确认配置

```bash
openclaw approvals get --gateway
openclaw config get tools.exec.host
openclaw config get tools.exec.security
openclaw config get tools.exec.ask
```

### 第二步：确认普通命令能跑

```bash
openclaw status
```

```bash
git status
```

```bash
node -e "console.log('NODE_OK')"
```

```bash
npm -v
```

### 第三步：再试复杂场景
例如：

- `npm run typecheck`
- `npm run build`
- 长时间运行命令
- 多命令串联
- 后台任务命令

如果只在复杂场景偶发弹条，那通常不是基础修复失效。

---

## 七、最短可复制版（懒人版）

如果你只想要最短步骤，就照这个顺序复制执行：

### 1. 设置 gateway approvals

```bash
openclaw approvals set --gateway --stdin
```

粘贴：

```json
{
  "version": 1,
  "defaults": {
    "security": "full",
    "ask": "off",
    "askFallback": "full"
  }
}
```

### 2. 设置 exec 配置

```bash
openclaw config set tools.exec.host gateway
openclaw config set tools.exec.security full
openclaw config set tools.exec.ask off
```

### 3. 重启 gateway

```bash
openclaw gateway restart
```

### 4. 验证

```bash
openclaw approvals get --gateway
openclaw config get tools.exec.host
openclaw config get tools.exec.security
openclaw config get tools.exec.ask
openclaw status
```

---

## 八、风险提醒

这套修复本质上是把 exec 调成：

```text
security = full
ask = off
```

优点：

- 不再频繁弹审批条
- 命令执行顺畅
- 很适合个人可信机器、闭环开发环境

风险：

- 安全边界明显放宽
- 如果这台机器暴露给开放频道、开放群组、危险 prompt 注入场景，风险会提高

所以请只在以下场景使用：

- 你自己的可信电脑
- 你明确知道这台 OpenClaw 是谁在用
- 你接受“更顺手，但更少审批”的取舍

---

## 九、如果以后要重新收紧安全边界

可以改回：

```bash
openclaw config set tools.exec.ask on
openclaw config set tools.exec.security allowlist
```

并重新设置 gateway approvals。

---

## 十、最后一句

如果你在另一台电脑上按这份教程做完后：

- 普通命令已经不弹条
- 但偶尔某些复杂命令还弹

那么优先判断为：

> “基础修复已生效，但还有个别特殊路径要继续查。”

不要直接判断成“整套修复失败”。

---

_这份教程就是为了跨机器复用而写，复制即用。_
