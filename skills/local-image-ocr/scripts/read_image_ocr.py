import argparse
import json
from pathlib import Path


def run_ocr(image_path: Path, lang: str = "ch") -> dict:
    result = {
        "ok": False,
        "engine": "paddleocr",
        "image": str(image_path),
        "text": "",
        "lines": [],
    }

    if not image_path.exists():
        result["error"] = "image_not_found"
        return result

    try:
        from paddleocr import PaddleOCR  # type: ignore
    except Exception as e:
        result["error"] = "paddleocr_not_installed"
        result["hint"] = f"Install dependencies first: {type(e).__name__}: {e}"
        return result

    try:
        ocr = PaddleOCR(use_angle_cls=True, lang=lang)
        raw = ocr.ocr(str(image_path), cls=True)

        lines = []
        texts = []
        for block in raw or []:
            for item in block or []:
                if not item or len(item) < 2:
                    continue
                box, meta = item[0], item[1]
                text = ""
                score = None
                if isinstance(meta, (list, tuple)) and len(meta) >= 1:
                    text = str(meta[0] or "").strip()
                    if len(meta) >= 2:
                        score = meta[1]
                if text:
                    texts.append(text)
                    lines.append({
                        "text": text,
                        "score": score,
                        "box": box,
                    })

        result["ok"] = True
        result["text"] = "\n".join(texts)
        result["lines"] = lines
        result["lineCount"] = len(lines)
        return result
    except Exception as e:
        result["error"] = "ocr_failed"
        result["hint"] = f"{type(e).__name__}: {e}"
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Read text from an image using PaddleOCR")
    parser.add_argument("--image", required=True, help="Path to image")
    parser.add_argument("--lang", default="ch", help="PaddleOCR language code, default: ch")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    payload = run_ocr(Path(args.image), lang=args.lang)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        if payload.get("ok") and payload.get("text"):
            print("\n===== OCR TEXT =====\n")
            print(payload["text"])

    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
