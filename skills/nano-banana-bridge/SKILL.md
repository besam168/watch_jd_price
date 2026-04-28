---
name: nano-banana-bridge
description: 本地 Nano Banana 风格生图桥接骨架。当前已支持接入 OpenAI-compatible 图像生成接口；保留 mock/dry-run 便于联调，默认不把密钥硬编码进脚本，优先从环境变量或命令行参数读取。
---

# nano-banana-bridge

这是一个 **Nano Banana 风格** 的本地生图 bridge skill。

当前目录结构：
- `SKILL.md`
- `scripts/generate_image.py`
- `output/`

## 适用场景
当用户想要：
- 文生图
- 图生图（若目标接口支持）
- 图片编辑（若目标接口支持）
- 指定尺寸/分辨率生成
- 通过 OpenAI-compatible / Gemini / FAL / 本地 SD / ComfyUI 接统一桥接

## 当前状态
当前已具备两种模式：

1. **mock / dry-run 模式**
   - 用于安全联调
   - 不真正调用外部接口

2. **OpenAI-compatible 图像生成模式**
   - 通过 `--provider openai-compatible`
   - 调用兼容 OpenAI 风格的图像生成 HTTP 接口
   - 默认从参数或环境变量读取：
     - `OPENAI_IMAGE_BASE_URL`
     - `OPENAI_IMAGE_API_KEY`
     - `OPENAI_IMAGE_MODEL`

## 设计原则
1. **先收桥接层，再按 provider 扩展**
2. **不默认把长期密钥硬编码进脚本**
3. **输出文件统一进入 `output/`**
4. **保留 mock / dry-run 便于排障**
5. **脚本尽量短、清楚、可审计**

## 当前命令示例

### 1）Mock 文生图
```powershell
python {baseDir}/scripts/generate_image.py --prompt "一只戴墨镜的橘猫，电影海报风格" --mock
```

### 2）Dry-run 预演
```powershell
python {baseDir}/scripts/generate_image.py --prompt "未来城市夜景" --provider openai-compatible --dry-run
```

### 3）真实调用 OpenAI-compatible 图像接口
```powershell
$env:OPENAI_IMAGE_BASE_URL="https://api-cn.hi-code.cc/v1"
$env:OPENAI_IMAGE_API_KEY="<your-key>"
$env:OPENAI_IMAGE_MODEL="gpt-image-1"
python {baseDir}/scripts/generate_image.py --prompt "未来城市夜景，电影感，超清" --provider openai-compatible --size 1024x1024
```

### 4）通过参数显式传入接口配置
```powershell
python {baseDir}/scripts/generate_image.py --prompt "黑金高级感产品海报" --provider openai-compatible --base-url "https://api-cn.hi-code.cc/v1" --api-key "<your-key>" --model "gpt-image-1"
```

## 说明
- 当前脚本优先实现 **文生图**。
- 不同 provider 的图像接口字段可能略有不同；当前按常见 OpenAI-compatible 形式优先兼容：
  - `POST /images/generations`
  - body 含 `model`、`prompt`、`size`
  - 响应中优先读取 `data[0].b64_json`，其次尝试 `data[0].url`
- 若目标接口只兼容 `/v1/responses` + `image_generation` 工具，则需要后续再补一层适配。

## 未来可接 provider
后续可以继续扩展到：
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
- `model`
- `baseUrl`

失败时输出 JSON，包含：
- `status=error`
- `error`
- 可选 `details`

## 当前建议
如果要正式使用：
1. 先用 `--dry-run` 验证参数
2. 再用一条简单 prompt 做真实出图
3. 验证接口实际返回结构后，再决定是否继续补图生图 / 编辑 / responses 兼容层
