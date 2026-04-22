from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def resolve_tesseract_path() -> str | None:
    direct = shutil.which("tesseract")
    if direct:
        return direct
    fallback_paths = [
        Path("C:/Program Files/Tesseract-OCR/tesseract.exe"),
        Path("C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"),
    ]
    for p in fallback_paths:
        if p.exists():
            return str(p)
    return None


def run() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "missing_image"}, ensure_ascii=False))
        return 2

    image_path = Path(sys.argv[1])
    expected = sys.argv[2] if len(sys.argv) > 2 else ""
    result: dict[str, object] = {
        "ok": False,
        "image": str(image_path),
        "expectedTitle": expected,
        "ocrAvailable": False,
        "titleMatched": False,
        "ocrText": "",
    }

    if not image_path.exists():
        result["error"] = "image_not_found"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    tesseract = resolve_tesseract_path()
    if not tesseract:
        result["error"] = "tesseract_not_found"
        result["checkedPaths"] = [
            "PATH:tesseract",
            "C:/Program Files/Tesseract-OCR/tesseract.exe",
            "C:/Program Files (x86)/Tesseract-OCR/tesseract.exe",
        ]
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    result["ocrAvailable"] = True

    try:
        completed = subprocess.run(
            [tesseract, str(image_path), "stdout", "-l", "eng+chi_sim"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
        text = (completed.stdout or "").strip()
        result["ocrReturnCode"] = completed.returncode
        result["ocrText"] = text[:4000]
        if expected:
            result["titleMatched"] = expected.lower() in text.lower()
        result["ok"] = completed.returncode == 0
        if completed.stderr:
            result["ocrStderr"] = (completed.stderr or "")[:1000]
    except Exception as e:
        result["error"] = str(e)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(run())
