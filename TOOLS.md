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

Add whatever helps you do your job. This is your cheat sheet.
