# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

### GitHub SSH 443 上传路线（2026-04-29 新增）
- 这台机器如果 `git@github.com:...` 的 22 端口 SSH 不通，直接切：`ssh.github.com:443`
- 首次执行：

```powershell
ssh -T -p 443 git@ssh.github.com
```

- 确认 `yes` 后，会把 `[ssh.github.com]:443` 写入 `known_hosts`
- 之后 remote 建议直接写成：

```powershell
ssh://git@ssh.github.com:443/<owner>/<repo>.git
```

- 推送模板：

```powershell
git remote set-url origin ssh://git@ssh.github.com:443/<owner>/<repo>.git
git push -u origin main
```

- 已真实跑通仓库：`office-productivity-skills`
- 2026-04-30 新增已跑通仓库：`global-news-mail`

### 独立仓库登记（2026-04-30 更新）
- `global-news-mail`
  - GitHub：`https://github.com/besam168/global-news-mail`
  - SSH remote：`ssh://git@ssh.github.com:443/besam168/global-news-mail.git`
  - 本地目录：`C:\Users\besam\.openclaw\workspace\global-news-mail`
  - 性质：**独立 Git 仓库**，不是总工作区普通目录
  - 维护规则：
    1. 以后改这个项目，优先在 `global-news-mail` 目录里单独 `git status / add / commit / push`
    2. 总工作区只保留入口/记忆/总览，不要把独立仓库内容再重复散拷到总仓
    3. 若总工作区需要记录它，只记录仓库指针、说明文档或相关记忆，不做双重主线维护

### 办公室软件 / 文档类插件（2026-04-29 整理）
- Word 简版生成：`docx-generator`
- Word 强编辑版：`minimax-docx`
- Excel / 表格：`minimax-xlsx`
- PPT / 演示文稿：`pptx-generator`
- Word 转 PDF：`word-to-pdf`
- 另一台电脑安装教程已写入：`办公软件插件安装教程.md`

## 生图链路工作区说明（2026-04-29 更新）

### nano-banana-bridge 当前正式用法
- 脚本位置：`skills/nano-banana-bridge/scripts/generate_image.py`
- 当前正式推荐参数：
  - `--provider openai-compatible`
  - `--api-mode images`
  - `--base-url "https://api-cn.hi-code.cc/v1"`
  - `--model "gpt-image-1"`
  - `--size "1536x1024"`（当前最稳）
- 正式调用模板：

```powershell
python skills\nano-banana-bridge\scripts\generate_image.py \
  --prompt "<你的中文 prompt>" \
  --provider openai-compatible \
  --api-mode images \
  --base-url "https://api-cn.hi-code.cc/v1" \
  --api-key "<key>" \
  --model "gpt-image-1" \
  --size "1536x1024"
```

### 已踩实的修复方法
1. 不再依赖 OpenClaw `image_generate` 默认 provider；改走本地 `nano-banana-bridge` 自控链路。
2. 不再把 `https://www.hi-code.cc/v1` 当正式默认图像入口；该地址今天连续返回 `403 / 1010`。
3. 不再把 `/responses + image_generation` 当正式口径；该兼容层会退化成普通文本输出。
4. 正式生产统一强制走：`/images/generations`。
5. prompt 要收敛：单张、中文直接描述、不要一次混太多复杂要求。
6. 高分辨率声明要克制：上游可能把 `4096x4096` 实际降回 `1024x1024`，所以必须以**真实返回 size**为准，不看请求值自我感动。

### 当前边界
- **已实测可用**：`1536x1024` 单张中文场景图
- **未完全踩实**：真 4K 稳定返回
- **后续策略**：先稳图，后超分；先实际返回，再对外宣称

### 美股默认查询口径（2026-04-30 新增）
- 以后大老板在聊天里只说：`美股` / `美股盘面` / `美股指数盘面`
- 默认一律按**真指数**查询，不用 ETF 代理顶替。
- 固定查询对象：
  - `^DJI` → 道琼斯工业指数
  - `^IXIC` → 纳斯达克综合指数
  - `^GSPC` → 标普500指数
- `SPY / QQQ / DIA` 只能作为 ETF 代理参考，**不能直接说成三大指数**。
- 默认回答结构：
  1. 三大真指数点位 + 涨跌幅
  2. 一句话盘面判断（强 / 弱 / 分化 / 震荡）
  3. 如用户继续追问，再补七巨头、科技权重、对A股映射
- 如果 `reports/scheduled/qveris_market_snapshot.json` 无效、过期、缺 `SPX / IXIC / DJI` 核心键，禁止直接拿缓存回；必须切实时行情链路。

