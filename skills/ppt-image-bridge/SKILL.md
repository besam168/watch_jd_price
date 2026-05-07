---
name: ppt-image-bridge
description: 稳态本地生图桥。用于通过 OpenAI-compatible Images API 以最小稳定面生成单张图片，优先解决编码、尺寸和返回格式稳定性问题。适用于需要稳定文生图、避免复杂比例映射、避免 responses fallback、固定使用少量正式尺寸，并已补充支持当前已明确可用的真 2K 尺寸组。
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
- 需要当前已明确可用的 **真 2K** 输出

## 设计原则
1. **只做单张图**：固定 `n=1`
2. **只走 Images API**：固定 `POST /images/generations`
3. **正式支持 8 个尺寸**：
   - `1024x1024`
   - `1536x1024`
   - `1024x1536`
   - `2048x1152`（16:9 真 2K）
   - `1536x1536`（1:1 真 2K）
   - `1152x1536`（9:16 真 2K）
   - `2048x1448`（3:2 真 2K）
   - `1448x2048`（2:3 真 2K）
4. **固定优先 `b64_json`**：成功后本地直接保存 PNG
5. **强制 UTF-8**：prompt / body / 保存日志全部按 UTF-8 处理
6. **错误分层清楚**：鉴权、编码、网络、上游、返回格式分别报错
7. **优先显式真尺寸**：不重新引入复杂比例抽象，但支持少量别名映射到正式尺寸
8. **边界说清楚**：当前只把已明确可用的 2K 比例纳入正式口径；`21:9 / 4:3 / 3:4` 暂不纳入正式支持

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

### 横版真 2K（16:9）
```powershell
python {baseDir}/scripts/generate_image_stable.py --prompt "欧洲高端汽车发布会主视觉，黑金科技感，电影级光影" --provider openai-compatible --base-url "https://api-cn.hi-code.cc/v1" --api-key "<your-key>" --model "gpt-image-2" --size "2048x1152"
```

### 方图真 2K（1:1）
```powershell
python {baseDir}/scripts/generate_image_stable.py --prompt "高级品牌KV，极简构图，精致光影" --provider openai-compatible --base-url "https://api-cn.hi-code.cc/v1" --api-key "<your-key>" --model "gpt-image-2" --size "1536x1536"
```

### 竖版真 2K（9:16）
```powershell
python {baseDir}/scripts/generate_image_stable.py --prompt "未来汽车广告竖版海报，质感强，光影克制" --provider openai-compatible --base-url "https://api-cn.hi-code.cc/v1" --api-key "<your-key>" --model "gpt-image-2" --size "1152x1536"
```

### 3:2 真 2K
```powershell
python {baseDir}/scripts/generate_image_stable.py --prompt "高级工业设计场景，产品摄影感，结构清晰" --provider openai-compatible --base-url "https://api-cn.hi-code.cc/v1" --api-key "<your-key>" --model "gpt-image-2" --size "2048x1448"
```

### 2:3 真 2K
```powershell
python {baseDir}/scripts/generate_image_stable.py --prompt "高级品牌海报，纵向构图，层次分明" --provider openai-compatible --base-url "https://api-cn.hi-code.cc/v1" --api-key "<your-key>" --model "gpt-image-2" --size "1448x2048"
```

## 支持的尺寸别名
当前脚本除显式尺寸外，还支持少量便捷写法：
- `2k-landscape` -> `2048x1152`
- `16:9+2k` -> `2048x1152`
- `2048*1152` -> `2048x1152`
- `2k-square` / `1:1+2k` -> `1536x1536`
- `2k-portrait` / `9:16+2k` -> `1152x1536`
- `2k-3:2` / `3:2+2k` -> `2048x1448`
- `2k-2:3` / `2:3+2k` -> `1448x2048`

正式生产仍推荐优先直接写显式尺寸。

## 真 2K 口径说明
当前纳入正式支持的真 2K 比例为：
- `1:1`
- `16:9`
- `9:16`
- `3:2`
- `2:3`

当前**不纳入正式支持**的 2K 比例：
- `21:9`
- `4:3`
- `3:4`

原因不是“永远不能做”，而是目前没有把这些比例收成正式稳态口径，不能对外装成已经稳定。

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
3. 优先用显式尺寸，尤其真 2K 直接写：
   - `2048x1152`
   - `1536x1536`
   - `1152x1536`
   - `2048x1448`
   - `1448x2048`
4. 若要支持更多比例或编辑模式，在下一版单独扩展，不混进当前稳版


