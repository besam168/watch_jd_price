import argparse
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps
import pytesseract
from pytesseract import Output

DEFAULT_LANG = "chi_sim+eng"
PREPROCESS_MODES = {
    "raw",
    "gray",
    "binary",
    "upscale2x",
    "gray_upscale2x",
    "high_contrast",
}
QUERY_MODES = {"contains", "exact"}


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = re.sub(r"\s+", " ", value).strip()
    return value.lower()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OCR on an image and emit JSON.")
    parser.add_argument("image_path")
    parser.add_argument("lang", nargs="?", default=DEFAULT_LANG)
    parser.add_argument("--preprocess", choices=sorted(PREPROCESS_MODES), default="gray_upscale2x")
    parser.add_argument("--x", type=int)
    parser.add_argument("--y", type=int)
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--query")
    parser.add_argument("--query-mode", choices=sorted(QUERY_MODES), default="contains")
    return parser.parse_args()


def apply_preprocess(image: Image.Image, mode: str) -> Image.Image:
    if mode == "raw":
        return image.copy()

    if mode == "gray":
        return ImageOps.grayscale(image)

    if mode == "binary":
        gray = ImageOps.grayscale(image)
        return gray.point(lambda p: 255 if p >= 160 else 0)

    if mode == "upscale2x":
        width, height = image.size
        return image.resize((max(1, width * 2), max(1, height * 2)), Image.Resampling.LANCZOS)

    if mode == "gray_upscale2x":
        gray = ImageOps.grayscale(image)
        width, height = gray.size
        return gray.resize((max(1, width * 2), max(1, height * 2)), Image.Resampling.LANCZOS)

    if mode == "high_contrast":
        gray = ImageOps.grayscale(image)
        contrasted = ImageEnhance.Contrast(gray).enhance(2.5)
        sharpened = ImageEnhance.Sharpness(contrasted).enhance(1.8)
        return sharpened.point(lambda p: 255 if p >= 145 else 0)

    return image.copy()


def clamp_roi(image: Image.Image, x, y, width, height):
    if x is None and y is None and width is None and height is None:
        return image, {"x": 0, "y": 0, "width": image.width, "height": image.height, "applied": False}

    roi_x = max(0, int(x or 0))
    roi_y = max(0, int(y or 0))
    max_width = max(0, image.width - roi_x)
    max_height = max(0, image.height - roi_y)
    roi_width = max(0, int(width if width is not None else max_width))
    roi_height = max(0, int(height if height is not None else max_height))
    roi_width = min(roi_width, max_width)
    roi_height = min(roi_height, max_height)

    if roi_width <= 0 or roi_height <= 0:
        raise ValueError("invalid ROI after clamping")

    cropped = image.crop((roi_x, roi_y, roi_x + roi_width, roi_y + roi_height))
    return cropped, {"x": roi_x, "y": roi_y, "width": roi_width, "height": roi_height, "applied": True}


def item_matches(normalized_text_value: str, normalized_query: str, query_mode: str) -> bool:
    if not normalized_query:
        return True
    if query_mode == "exact":
        return normalized_text_value == normalized_query
    return normalized_query in normalized_text_value


def main() -> int:
    args = parse_args()
    image_path = Path(args.image_path).expanduser()
    lang = args.lang.strip() if args.lang and args.lang.strip() else DEFAULT_LANG

    if not image_path.exists():
        print(json.dumps({"ok": False, "error": f"image not found: {image_path}"}, ensure_ascii=False))
        return 1

    tesseract_cmd = os.environ.get("TESSERACT_CMD") or r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if Path(tesseract_cmd).exists():
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    try:
        original_image = Image.open(image_path)
        roi_image, roi = clamp_roi(original_image, args.x, args.y, args.width, args.height)
        processed_image = apply_preprocess(roi_image, args.preprocess)

        full_text = pytesseract.image_to_string(processed_image, lang=lang)
        data = pytesseract.image_to_data(processed_image, lang=lang, output_type=Output.DICT)
        normalized_query = normalize_text(args.query or "")

        items = []
        item_count = len(data.get("text", []))
        for i in range(item_count):
            text = (data["text"][i] or "").strip()
            if not text:
                continue

            try:
                conf = float(data["conf"][i])
            except Exception:
                conf = -1
            if conf < 0:
                continue

            left = int(data["left"][i])
            top = int(data["top"][i])
            width = int(data["width"][i])
            height = int(data["height"][i])
            abs_x = roi["x"] + left
            abs_y = roi["y"] + top
            normalized = normalize_text(text)
            matched = item_matches(normalized, normalized_query, args.query_mode)
            if not matched:
                continue

            items.append({
                "text": text,
                "normalizedText": normalized,
                "confidence": conf,
                "x": abs_x,
                "y": abs_y,
                "w": width,
                "h": height,
                "centerX": abs_x + (width / 2.0),
                "centerY": abs_y + (height / 2.0),
            })

        result = {
            "ok": True,
            "image": str(image_path),
            "lang": lang,
            "tesseract": pytesseract.pytesseract.tesseract_cmd,
            "preprocess": args.preprocess,
            "query": args.query or None,
            "queryMode": args.query_mode,
            "roi": roi,
            "text": full_text,
            "normalizedText": normalize_text(full_text),
            "count": len(items),
            "items": items,
        }
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
