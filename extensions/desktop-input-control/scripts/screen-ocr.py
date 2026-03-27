import json
import os
import sys
from pathlib import Path

from PIL import Image
import pytesseract
from pytesseract import Output


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "usage: screen-ocr.py <image_path> [lang]"}, ensure_ascii=False))
        return 1

    image_path = Path(sys.argv[1]).expanduser()
    lang = sys.argv[2] if len(sys.argv) >= 3 and sys.argv[2].strip() else "eng"

    if not image_path.exists():
        print(json.dumps({"ok": False, "error": f"image not found: {image_path}"}, ensure_ascii=False))
        return 1

    tesseract_cmd = os.environ.get("TESSERACT_CMD") or r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if Path(tesseract_cmd).exists():
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    image = Image.open(image_path)
    full_text = pytesseract.image_to_string(image, lang=lang)
    data = pytesseract.image_to_data(image, lang=lang, output_type=Output.DICT)

    items = []
    n = len(data.get("text", []))
    for i in range(n):
        text = (data["text"][i] or "").strip()
        if not text:
            continue
        try:
            conf = float(data["conf"][i])
        except Exception:
            conf = -1
        if conf < 0:
            continue
        items.append({
            "text": text,
            "confidence": conf,
            "x": int(data["left"][i]),
            "y": int(data["top"][i]),
            "w": int(data["width"][i]),
            "h": int(data["height"][i]),
        })

    result = {
        "ok": True,
        "image": str(image_path),
        "lang": lang,
        "tesseract": pytesseract.pytesseract.tesseract_cmd,
        "text": full_text,
        "count": len(items),
        "items": items,
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
