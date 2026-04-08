# OpenClaw 关闭“放行条 / 审批条”教程

> 适用场景：在 OpenClaw Control UI / WebChat 里执行本机命令时，频繁弹出 exec 放行条（approval popup / 审批条 / 放行条），影响连续工作。

---

## 一、问题现象

常见表现：

- 在控制台、WebChat、control-ui 中执行命令时，经常弹出“放行条”
- 即使只是跑 `openclaw status`、`git status`、`npm run typecheck` 这类常规命令，也会要求批准
- 命令本身没问题，但每次执行都被审批打断

---

## 二、先说结论：真正生效的是“两层配置”

很多人会误以为，只改一处就够了。实际上这类审批条通常由**两层配置共同决定**：

### 第 1 层：请求侧（OpenClaw 工具请求配置）
也就是 `tools.exec.*`

关键项：

- `tools.exec.host`
- `tools.exec.security`
- `tools.exec.ask`

### 第 2 层：Gateway 主机侧审批策略
也就是 gateway approvals 文件（`exec-approvals.json`）

关键项：

- `defaults.security`
- `defaults.ask`
- `defaults.askFallback`

> 只有**请求侧**和**gateway 审批侧**同时放开，exec 才能真正做到“不再弹放行条”。

---

## 三、已验证有效的修复步骤

以下步骤已在本机真实验证过可用。

### 步骤 1：把 gateway approvals 默认策略调成 ask=off

运行：

```bash
openclaw approvals set --gateway --stdin
```

然后输入：

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

这一步的作用：

- 告诉 gateway 主机：默认不要再弹审批条
- 同时保留 full 权限执行能力

---

### 步骤 2：把 OpenClaw 请求侧配置对齐

依次运行：

```bash
openclaw config set tools.exec.host gateway
openclaw config set tools.exec.security full
openclaw config set tools.exec.ask off
```

这一步的作用：

- 强制 exec 走 gateway
- 请求侧明确声明：本次执行不主动 ask
- 避免出现“gateway 放开了，但请求侧自己又要求 ask”的情况

---

### 步骤 3：重启 gateway

运行：

```bash
openclaw gateway restart
```

这一步很重要。

如果不重启，旧进程有时可能还拿着旧策略，表现会像“明明改了配置但还是弹条”。

---

## 四、如何核验是否修好

### 1）检查 gateway approvals

运行：

```bash
openclaw approvals get --gateway
```

理想结果应包含：

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

理想结果应分别是：

```text
gateway
full
off
```

---

### 3）做最小真测

可执行几条简单命令，例如：

```bash
openclaw status
```

```bash
git -C C:\Users\besam\.openclaw\workspace status --short
```

```bash
node -e "console.log('NODE_OK')"
```

```bash
npm -v
```

如果这些命令都能直接跑，不再弹条，说明主路径已经修好。

---

## 五、这次真实排查得到的经验

### 经验 1：昨天的修复并没有失效
本机再次核验时，以下配置依旧存在：

#### 请求侧：

- `tools.exec.host = gateway`
- `tools.exec.security = full`
- `tools.exec.ask = off`

#### gateway 审批侧：

- `security=full`
- `ask=off`
- `askFallback=full`

说明：

> 如果后来又偶发弹条，不一定代表配置被打回原样。

---

### 经验 2：普通命令无法稳定复现弹条
后续最小复现排查中，以下命令都能直接执行：

- `openclaw config get tools.exec.ask`
- `openclaw approvals get --gateway`
- `openclaw status`
- `git status`
- `node -e ...`
- `npm -v`
- `npm run typecheck`
- 本地 Node 测试脚本

说明：

> 当前问题更像“偶发命中特殊路径”，而不是“所有 exec 又重新坏了”。

---

### 经验 3：不要把偶发 UI 条误判成全局失效
如果偶尔又看到一次放行条，优先怀疑：

- 某条命令走了特殊执行路径
- 某次请求没有按标准 gateway full/off 配置落地
- 前端残留了旧的审批条
- 某个复杂场景命中了不同分支

不要第一时间就判断：

> “昨天的修复全失效了。”

---

## 六、如果以后又遇到放行条，怎么排查

建议按下面顺序：

### 第一步：先确认配置还在

```bash
openclaw approvals get --gateway
openclaw config get tools.exec.host
openclaw config get tools.exec.security
openclaw config get tools.exec.ask
```

如果结果仍然是：

- gateway approvals: `ask=off`
- tools.exec.ask: `off`

那就说明主配置还在。

---

### 第二步：做最小复现

先试这几类：

- OpenClaw CLI：`openclaw status`
- Git：`git status`
- Node：`node -e ...`
- NPM：`npm -v`

如果这些都不弹条，说明不是全局性故障。

---

### 第三步：定位是哪种“复杂场景”会触发

继续试：

- 长时间运行命令
- 后台 session 命令
- 多命令串联
- build + test + commit 组合
- 特定工具调用路径

这样才能抓到“漏点”。

---

## 七、风险提醒

这套做法的本质是：

```text
security = full
ask = off
```

优点：

- 很顺手
- 不再频繁打断工作
- 适合可信本机、个人控制台、闭环开发环境

风险：

- 安全边界明显放宽
- 如果开放频道、开放群聊、危险 prompt 注入场景存在，风险会上升

所以这套方法只适合：

- 本机可信环境
- 自己控制的 OpenClaw 实例
- 你明确接受更高便利性、较低审批阻力

如果以后要重新收紧安全边界，优先从这两处回调：

```bash
openclaw approvals get --gateway
openclaw approvals set --gateway --stdin
```

和：

```bash
openclaw config set tools.exec.ask on
openclaw config set tools.exec.security allowlist
```

---

## 八、最短版修复口令（备忘）

### 1. 设 gateway approvals

```bash
openclaw approvals set --gateway --stdin
```

输入：

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

### 2. 设请求侧

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

## 九、当前状态总结

截至本次记录：

- 关闭审批条的方法仍然有效
- 当前机器配置仍保持正确
- 普通命令无法稳定复现放行条
- 偶发条更像特殊路径 / 残留 UI，而不是修复整体失效

---

_作者备注：这份教程来自本机真实排障结果，不是纸上整理。以后若再次遇到同类问题，先按本教程核验，再决定是否继续做复杂场景复现。_
