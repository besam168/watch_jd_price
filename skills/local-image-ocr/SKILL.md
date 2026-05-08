---
name: local-image-ocr
summary: 使用本地 PaddleOCR 读取图片中的文字，适合 QQ 收图、试卷、截图、界面文字等中文 OCR 场景。
---

# local-image-ocr

本地读图 OCR 技能骨架。

## 目标
- 读取 QQ 收到的图片
- 读取试卷 / 截图 / 界面文字
- 先解决“看清图片里写了什么”
- 暂不把“看完后自动操作”作为首版必达目标

## 当前状态
- **已完成：** 技能骨架与调用脚本已建立
- **待完成：** 安装 `paddleocr` / `paddlepaddle` 依赖后做真实验收

## 运行方式
```bash
python skills/local-image-ocr/scripts/read_image_ocr.py --image <图片路径>
```

可选参数：
```bash
python skills/local-image-ocr/scripts/read_image_ocr.py --image <图片路径> --lang ch --json
```

## 输出
默认输出 JSON，字段包括：
- `ok`
- `engine`
- `image`
- `text`
- `lines`
- `error`
- `hint`

## 依赖
建议安装：
- `paddleocr`
- `paddlepaddle`
- `Pillow`

示例（仅记录，不在本技能内自动安装）：
```bash
python -m pip install paddleocr paddlepaddle Pillow
```

## 说明
- 当前机器已确认 `PIL` 可用，但 `paddleocr` / `paddle` 还未安装。
- 因此首版先把技能骨架与统一输出口搭好，后续补装依赖即可直接验收。
