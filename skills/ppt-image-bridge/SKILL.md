---
name: ppt-image-bridge
description: 稳态本地生图桥。用于通过 OpenAI-compatible Images API 以最小稳定面生成单张图片，优先解决编码、尺寸和返回格式稳定性问题。适用于需要稳定文生图、避免复杂比例映射、避免 responses fallback、固定使用少量正式尺寸，并已补充支持横版真 2K `2048x1152` 的场景。
---

# ppt-image-bridge

这是一个**正式生产优先、稳而不是花哨**的本地生图 skill。

## 何时使用
当用户要：
- 稳定文生图
- 通过 OpenAI-compatible `/images/generations` 生成图片
- 避免复杂 aspect ratio / resolution 映射
- 避免 `responses` 路线的不确定性
- 避免中文或特殊字符导致的编码坑
- 固定使用少数稳定尺寸进行正式输出
- 需要横版 **真 2K `2048x1152`** 输出

## 设计原则
1. **只做单张图**：固定 `n=1`
2. **只走 Images API**：固定 `POST /images/generations`
3. **正式支持 4 个尺寸**：
   - `1024x1024`
   - `1536x1024`
   - `1024x1536`
   - `2048x1152`（横版真 2K / 16:9）
4. **固定优先 `b64_json`**：成功后本地直接保存 PNG
5. **强制 UTF-8**：prompt / body / 保存日志全部按 UTF-8 处理
6. **错误分层清楚**：鉴权、编码、网络、上游、返回格式分别报错
7. **优先显式真尺寸**：不重新引入复杂比例抽象，但支持少量别名映射到正式尺寸

## 当前目录结构
- `SKILL.md`
- `scripts/generate_image_stable.py`
- `output/`

## 当前调用方式

### 最稳竖图
```powershell
python {baseDir}/scripts/generate_image_stable.py --prompt "夕阳海边人像，电影感，真实皮肤质感" --provider openai-compatible --base-url "https://api-cn.hi-code.cc/v1" --api-key "<your-key>" --model "gpt-image-2" --size "1024x1536"
```

### 最稳横图
```powershell
python {baseDir}/scripts/generate_image_stable.py --prompt "未来城市夜景，电影感" --provider openai-compatible --base-url "https://api-cn.hi-code.cc/v1" --api-key "<your-key>" --model "gpt-image-2" --size "1536x1024"
```

### 横版真 2K（正式新增）
```powershell
python {baseDir}/scripts/generate_image_stable.py --prompt "欧洲高端汽车发布会主视觉，黑金科技感，电影级光影" --provider openai-compatible --base-url "https://api-cn.hi-code.cc/v1" --api-key "<your-key>" --model "gpt-image-2" --size "2048x1152"
```

### 正方形
```powershell
python {baseDir}/scripts/generate_image_stable.py --prompt "黑金高级感产品海报" --provider openai-compatible --base-url "https://api-cn.hi-code.cc/v1" --api-key "<your-key>" --model "gpt-image-2" --size "1024x1024"
```

## 支持的尺寸别名
当前脚本除显式尺寸外，还支持少量便捷写法：
- `2k-landscape` -> `2048x1152`
- `16:9+2k` -> `2048x1152`
- `2048*1152` -> `2048x1152`

正式生产仍推荐优先直接写：`2048x1152`

## 限制
- 当前**不支持**：
  - `responses` fallback
  - `1K/2K/4K` 全套抽象档位
  - 8 比例自动映射
  - 单次多图
  - 自动编辑 / 图生图
- 当前策略仍是：**少量正式尺寸 + 稳定输出优先**
- 如果用户要更高分辨率或更多比例，先以正式尺寸稳定出图，再考虑下一版扩展

## 输出规范
成功时输出 JSON，包含：
- `status=success`
- `provider`
- `model`
- `baseUrl`
- `requestedSize`
- `size`
- `output`
- `responseFormat`

失败时输出 JSON，包含：
- `status=error`
- `errorCode`
- `error`
- `provider`
- `model`
- `baseUrl`
- `requestedSize`

## 当前建议
如果目标是正式生产：
1. 先用英文或纯 ASCII prompt 做最小真测
2. 再用真实 prompt
3. 优先用显式尺寸，尤其真 2K 横图直接写：`2048x1152`
4. 若要支持更多比例或编辑模式，在下一版单独扩展，不混进当前稳版

