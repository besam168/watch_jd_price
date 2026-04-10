---
name: nano-banana-bridge
description: 本地 Nano Banana 风格生图桥接骨架。用于后续接入真实图像生成/编辑 provider。当前版本先提供安全骨架、参数约定、输出目录规范与占位脚本，不默认携带任何外部 API 密钥。
---

# nano-banana-bridge

这是一个 **Nano Banana 风格** 的本地 skill 骨架，参考了 ClawHub 上同类生图 skill 的轻量结构：

- `SKILL.md`
- `scripts/generate_image.py`

## 适用场景
当用户想要：
- 文生图
- 图生图
- 图片编辑
- 指定尺寸/分辨率生成
- 后续接入 Gemini / FAL / 其他图像生成 API

## 当前状态
当前是 **安全骨架版**：
- 已定义输入参数
- 已定义输出目录
- 已定义成功/失败返回格式
- 已支持 dry-run / mock 结果
- **尚未默认接入真实第三方 API**

这样做的目的，是先把 skill 结构、调用约定、输出路径、可维护性收好，再决定接哪个 provider。

## 目录结构
- `{baseDir}/SKILL.md`
- `{baseDir}/scripts/generate_image.py`
- `{baseDir}/output/`

## 设计原则
1. **先收骨架，后接 provider**
2. **不默认捆绑长期密钥**
3. **输出文件统一进入 output/**
4. **先支持 mock，再切真实调用**
5. **尽量保持脚本短、清楚、可审计**

## 当前命令示例
### 1）Mock 文生图
```powershell
python {baseDir}/scripts/generate_image.py --prompt "一只戴墨镜的橘猫，电影海报风格" --mock
```

### 2）Mock 图生图
```powershell
python {baseDir}/scripts/generate_image.py --prompt "把这张图改成赛博朋克风格" --input-image C:\path\to\input.png --mock
```

### 3）指定输出尺寸
```powershell
python {baseDir}/scripts/generate_image.py --prompt "未来城市夜景" --size 1536x1024 --mock
```

## 未来可接 provider
后续可以切到任意一种：
- Gemini 图像模型
- FAL
- OpenAI image generation
- 其他 OpenAI-compatible 图像接口
- 本地 SD WebUI / ComfyUI

## 输出规范
成功时输出 JSON，包含：
- `status`
- `mode`
- `prompt`
- `inputImage`
- `output`
- `size`
- `provider`

失败时输出 JSON，包含：
- `status=error`
- `error`

## 当前建议
先把这个骨架跑通，再决定是否：
1. 做 Gemini 版
2. 做 OpenAI-compatible 版
3. 做本地 ComfyUI / SD 版
