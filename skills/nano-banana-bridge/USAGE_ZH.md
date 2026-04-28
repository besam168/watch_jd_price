# nano-banana-bridge 使用教程

这份教程给大老板直接用，讲人话，不绕。

---

## 这是什么

`nano-banana-bridge` 现在已经不是纯 mock 骨架了。
它已经可以通过 **OpenAI-compatible 图像接口** 真实生图。

当前已接通：
- Base URL：`https://api-cn.hi-code.cc/v1`
- Model：`gpt-image-1`

脚本位置：
- `skills/nano-banana-bridge/scripts/generate_image.py`

输出目录：
- `skills/nano-banana-bridge/output/`

---

## 现在支持什么

### 1）文生图
输入一段提示词，直接生成图片。

### 2）两种尺寸写法

#### 写法 A：直接写像素尺寸
例如：
- `--size 2048x1152`
- `--size 1024x1024`

#### 写法 B：写“比例 + 分辨率档位”
例如：
- `--aspect-ratio 16:9 --resolution 2K`
- `--aspect-ratio 1:1 --resolution 4K`

这个写法更适合以后长期固定使用。

---

## 支持多少种比例

当前支持 **8 种比例**：

1. `1:1`
2. `3:2`
3. `2:3`
4. `16:9`
5. `9:16`
6. `4:3`
7. `3:4`
8. `21:9`

---

## 支持多少种分辨率档位

当前支持 **3 种分辨率档位**：

1. `1K`
2. `2K`
3. `4K`

---

## 比例和分辨率怎么映射

### 1:1
- 1K → `1024x1024`
- 2K → `2048x2048`
- 4K → `4096x4096`

### 3:2
- 1K → `1536x1024`
- 2K → `2304x1536`
- 4K → `4608x3072`

### 2:3
- 1K → `1024x1536`
- 2K → `1536x2304`
- 4K → `3072x4608`

### 16:9
- 1K → `1792x1024`
- 2K → `2048x1152`
- 4K → `4096x2304`

### 9:16
- 1K → `1024x1792`
- 2K → `1152x2048`
- 4K → `2304x4096`

### 4:3
- 1K → `1365x1024`
- 2K → `2731x2048`
- 4K → `5461x4096`

### 3:4
- 1K → `1024x1365`
- 2K → `2048x2731`
- 4K → `4096x5461`

### 21:9
- 1K → `2389x1024`
- 2K → `4779x2048`
- 4K → `9557x4096`

注意：
这些是插件侧的映射规则。
**最终某个尺寸是否被上游接口接受，还是以真实接口返回为准。**

---

## 最常用命令

### 1）最稳的 2K 横版项目图
```powershell
python skills\nano-banana-bridge\scripts\generate_image.py --prompt "你的提示词" --provider openai-compatible --base-url "https://api-cn.hi-code.cc/v1" --api-key "你的key" --model "gpt-image-1" --aspect-ratio 16:9 --resolution 2K
```

### 2）直接指定真 2K 尺寸
```powershell
python skills\nano-banana-bridge\scripts\generate_image.py --prompt "你的提示词" --provider openai-compatible --base-url "https://api-cn.hi-code.cc/v1" --api-key "你的key" --model "gpt-image-1" --size 2048x1152
```

### 3）先 dry-run 看参数有没有对上
```powershell
python skills\nano-banana-bridge\scripts\generate_image.py --prompt "测试提示词" --provider openai-compatible --aspect-ratio 16:9 --resolution 2K --dry-run
```

### 4）先设环境变量，再简化命令
```powershell
$env:OPENAI_IMAGE_BASE_URL="https://api-cn.hi-code.cc/v1"
$env:OPENAI_IMAGE_API_KEY="你的key"
$env:OPENAI_IMAGE_MODEL="gpt-image-1"

python skills\nano-banana-bridge\scripts\generate_image.py --prompt "你的提示词" --provider openai-compatible --aspect-ratio 16:9 --resolution 2K
```

---

## 适合怎么用

这条链路现在特别适合：

- 小学生创新项目图
- 比赛展板主视觉
- 项目外观图
- 社区使用场景图
- 功能流程示意图
- 中文手绘风概念图

尤其适合：
- **16:9 + 2K**
- 做项目展示材料很稳

---

## 当前还没补的

现在已经能正式文生图，但还有边界：

1. **图生图还没补**
   - `--input-image` 在 openai-compatible 模式下还没实现

2. **图片编辑还没补**
   - 现在优先是文生图

3. **/v1/responses + image_generation 兼容层还没补**
   - 当前优先用 `/images/generations`

---

## 最短实用结论

如果以后要快速出图，默认记这条就够了：

```powershell
python skills\nano-banana-bridge\scripts\generate_image.py --prompt "你的提示词" --provider openai-compatible --base-url "https://api-cn.hi-code.cc/v1" --api-key "你的key" --model "gpt-image-1" --aspect-ratio 16:9 --resolution 2K
```

这就是现在最稳的项目图打法。
