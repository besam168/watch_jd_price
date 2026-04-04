from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
CAPTURE_PS = ROOT / "scripts" / "screen-capture-compat.ps1"
OCR_PY = ROOT / "scripts" / "screen-ocr.py"
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(parents=True, exist_ok=True)


def run_capture(path: Path) -> None:
    cmd = [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(CAPTURE_PS),
        str(path),
        "-VirtualScreen",
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")


def run_ocr(image_path: Path, x: int, y: int, width: int, height: int, query: str = "") -> dict[str, Any]:
    cmd = [
        "python",
        str(OCR_PY),
        str(image_path),
        "chi_sim+eng",
        "--preprocess",
        "gray_upscale2x",
        "--x",
        str(x),
        "--y",
        str(y),
        "--width",
        str(width),
        "--height",
        str(height),
        "--group-by",
        "line",
        "--top-n",
        "8",
        "--engine",
        "auto",
    ]
    if query:
        cmd.extend(["--query", query])
    completed = subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return json.loads(completed.stdout)


def normalize_lines(payload: dict[str, Any]) -> list[str]:
    items = payload.get("items") or payload.get("matches") or []
    out: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        if text:
            out.append(text)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="QQ window helper for search-state diagnostics")
    parser.add_argument("--contact", required=True, help="Target contact text, e.g. 新干线")
    parser.add_argument("--search-x", type=int, default=120)
    parser.add_argument("--search-y", type=int, default=70)
    parser.add_argument("--search-width", type=int, default=280)
    parser.add_argument("--search-height", type=int, default=90)
    parser.add_argument("--results-x", type=int, default=0)
    parser.add_argument("--results-y", type=int, default=120)
    parser.add_argument("--results-width", type=int, default=420)
    parser.add_argument("--results-height", type=int, default=700)
    args = parser.parse_args()

    shot = ARTIFACTS / "qq-search-diagnostic.png"
    run_capture(shot)

    search_ocr = run_ocr(shot, args.search_x, args.search_y, args.search_width, args.search_height)
    results_ocr = run_ocr(shot, args.results_x, args.results_y, args.results_width, args.results_height, query=args.contact)

    search_lines = normalize_lines(search_ocr)
    result_lines = normalize_lines(results_ocr)
    result_blob = "\n".join(result_lines)
    target_found = args.contact in result_blob

    output = {
        "ok": True,
        "imagePath": str(shot),
        "target": args.contact,
        "searchRegion": {
            "x": args.search_x,
            "y": args.search_y,
            "width": args.search_width,
            "height": args.search_height,
            "lines": search_lines,
        },
        "resultsRegion": {
            "x": args.results_x,
            "y": args.results_y,
            "width": args.results_width,
            "height": args.results_height,
            "lines": result_lines,
        },
        "targetFound": target_found,
    }
    sys.stdout.write(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
