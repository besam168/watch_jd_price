#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCREEN_OCR = ROOT / "scripts" / "screen-ocr.py"
CALIBRATION = ROOT / "scripts" / "coordinate-calibration.py"
CLEANER = ROOT / "scripts" / "clean-chinese-ocr-box.py"
PYTHON = Path(r"C:\Users\besam\AppData\Local\Programs\Python\Python312\python.exe")


def run_json(cmd: list[str]) -> dict:
    completed = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if completed.returncode != 0:
        raise RuntimeError(f"command failed rc={completed.returncode}\nstdout={completed.stdout}\nstderr={completed.stderr}")
    return json.loads(completed.stdout)


def normalize_text(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def contains_chars(haystack: str, needle: str) -> bool:
    h = (haystack or "").replace(" ", "")
    n = (needle or "").replace(" ", "")
    return bool(n) and n in h


def main() -> int:
    parser = argparse.ArgumentParser(description="Locate OCR text box without passing Chinese query into OCR CLI")
    parser.add_argument("image")
    parser.add_argument("query")
    parser.add_argument("--top-n", type=int, default=80)
    args = parser.parse_args()

    ocr_result = run_json([
        str(PYTHON),
        str(SCREEN_OCR),
        str(Path(args.image).resolve()),
        "--top-n",
        str(args.top_n),
        "--group-by",
        "phrase",
    ])

    items = ocr_result.get("items", []) or []
    target = None
    query_norm = normalize_text(args.query)

    for item in items:
        text = item.get("text", "") or ""
        item_norm = normalize_text(text)
        if query_norm and query_norm in item_norm:
            target = item
            break
        if contains_chars(text, args.query):
            target = item
            break

    if target is None:
        print(json.dumps({
            "ok": False,
            "error": f"query not found: {args.query}",
            "sampleTexts": [item.get("text", "") for item in items[:20]],
        }, ensure_ascii=False, indent=2))
        return 1

    cleaned = run_json([
        str(PYTHON),
        str(CLEANER),
        str(write_temp_target(target)),
    ])
    clean_box = cleaned.get("box") or target

    center_x = float(clean_box.get("centerX", 0.0))
    center_y = float(clean_box.get("centerY", 0.0))

    mapped = run_json([
        str(PYTHON),
        str(CALIBRATION),
        "convert",
        str(center_x),
        str(center_y),
    ])

    result = {
        "ok": True,
        "query": args.query,
        "ocrBox": {
            "text": target.get("text"),
            "x": target.get("x"),
            "y": target.get("y"),
            "w": target.get("w"),
            "h": target.get("h"),
            "centerX": float(target.get("centerX", 0.0)),
            "centerY": float(target.get("centerY", 0.0)),
            "confidence": target.get("confidence"),
            "parts": target.get("parts", []),
        },
        "cleanedBox": clean_box,
        "cleanMode": cleaned.get("mode"),
        "clusters": cleaned.get("clusters", []),
        "mappedClick": mapped.get("output"),
        "screen": mapped.get("screen"),
        "model": mapped.get("model"),
    }
    safe_print_json(result)
    return 0


def write_temp_target(target: dict) -> Path:
    tmp = ROOT / "artifacts" / "tmp_clean_target.json"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps({"item": target}, ensure_ascii=False, indent=2), encoding="utf-8")
    return tmp


def safe_print_json(payload: dict) -> None:
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    try:
        print(text)
    except UnicodeEncodeError:
        import sys
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))


if __name__ == "__main__":
    raise SystemExit(main())
