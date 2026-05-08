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

### 生图默认正式入口（2026-04-30 更新）
- 以后大老板在聊天里只要直接说：`生图`
- 默认不要再先走 OpenClaw 自带 `image_generate` 试错
- 默认对外名称按：`ppt-image-bridge`
- 当前工作区正式目录：`skills/ppt-image-bridge/`
- 正式默认链路固定为：
  - provider：`openai-compatible`
  - base_url：`https://api-cn.hi-code.cc/v1`
  - model：`gpt-image-1`
  - endpoint：`/images/generations`
- 正式默认尺寸只先用稳定三档：
  - `1024x1024`
  - `1536x1024`
  - `1024x1536`
- 其中：
  - 竖图默认优先：`1024x1536`
  - 横图默认优先：`1536x1024`
- `https://www.hi-code.cc/v1` 今天已再次实测确认会触发 Cloudflare `403 / 1010 / browser_signature_banned`，以后**不再当默认正式入口**。
- 核心脚本：`skills/ppt-image-bridge/scripts/generate_image_stable.py`
- 已真实成功出图文件：`skills/ppt-image-bridge/output/stable-image_20260430_151616.png`
- 正式仓库：`https://github.com/besam168/ppt-image-bridge`
- 正式仓 SSH remote：`ssh://git@ssh.github.com:443/besam168/ppt-image-bridge.git`
- 当前默认分工：
  - `ppt-image-bridge` = 正式生产仓，默认稳定出图、PPT 配图、中文说明图、日常交付都先走这条；
  - `ppt-image-bridge-v2-lab` = Images 2.0 / `gpt-image-2` 实验仓，专门测中文排版、2K/4K、多比例与新能力，不默认替代正式版；
- v2 实验仓：`https://github.com/besam168/ppt-image-bridge-v2-lab`
- v2 实验仓 SSH remote：`ssh://git@ssh.github.com:443/besam168/ppt-image-bridge-v2-lab.git`
- 截至 2026-04-30 已踩实的 `gpt-image-2` 2K 可用比例：
  - `1:1`
  - `16:9`
  - `9:16`
  - `3:2`
  - `2:3`
- 当前失败/不稳：
  - `16:9 + 4K`
  - `21:9 + 2K`
  - `4:3 + 2K`
  - `3:4 + 2K`
- 执行纪律：以后生图链路默认由我直接接管，不再把命令丢给大老板手动折腾。

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

### OpenClaw 版本回溯 / 降级注意（2026-05-08 新增）
- 这台机器当前确认过的版本线索：
  1. **当前版本**：`v2026.4.2`
  2. **当前全局 npm 安装目录创建时间**：`2026-04-03 10:26:47`
  3. **本机 OpenClaw 首次初始化时间**：`2026-03-13 23:15~23:16`
- 已查实：
  - npm 上存在：`openclaw@2026.3.12`
  - GitHub tags 上存在：`v2026.3.12`
- 当前最稳推断：
  1. 首装时间大概率是：`2026-03-13` 晚上
  2. 首装版本大概率是：`2026.3.12`
  3. 到 `2026-03-25` 左右，这套环境已出现 `2026.3.13` 痕迹
  4. 现在这份 `v2026.4.2` 是后续升级版本，不是首装版本
- 以后如果大老板再提“降回 3.12 / 回老版本试试”，默认先记住：
  1. **技术上大概率可降级**，因为 `2026.3.12` 真实存在且可安装
  2. **不要直接在主环境硬降**
  3. 优先做法是：**并行验证 / 临时环境验证 / 先备份 `C:\Users\besam\.openclaw` 再试**
  4. 风险点主要是：
     - `openclaw.json` 配置结构可能不兼容
     - QQBot / 新插件 / task / flow / approvals 等后期能力可能不兼容
     - `.openclaw/` 下状态数据可能带有高版本迁移痕迹，老版本未必能吃下
- 因此以后默认口径：
  - **3.12 有**
  - **理论上可降**
  - **正式操作前先做隔离验证，不直接动生产主环境**

### desktop-web-workflow 脚本1 固定口令（2026-05-08 新增）
- 以后大老板在聊天里只要说：`脚本1`
- 默认就理解为：运行 `desktop-web-workflow` 的脚本1，而**不是**截图脚本
- 当前固定行为：
  1. 识别目标浏览器窗口（`OpenClaw Control - Google Chrome`）
  2. 在已验证的输入框相对位置点击
  3. **输入：`继续`**
  4. **然后回车**
- 同义口令一并视为相同意思：
  - `启动脚本1`
  - `起动脚本1`
  - `跑脚本1`
- 如果大老板明确说：`截图`，那才走 `qq-screenshot`
- 以后不要再把“脚本1”误解成截图方案 `pil/system`
- 当前脚本位置：`skills/desktop-web-workflow/scripts/script1_runner.py`

