from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
DESKTOP_PY = ROOT / "scripts" / "desktop-input.py"
HELPER_PY = ROOT / "scripts" / "qq-search-helper.py"


def run_desktop(args: list[str]) -> Any:
    completed = subprocess.run(
        ["python", str(DESKTOP_PY), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    stdout = (completed.stdout or "").strip()
    try:
        return json.loads(stdout)
    except Exception:
        return stdout


def run_helper(contact: str, results_x: int, results_y: int, results_width: int, results_height: int) -> dict[str, Any]:
    completed = subprocess.run(
        [
            "python",
            str(HELPER_PY),
            "--contact",
            contact,
            "--results-x",
            str(results_x),
            "--results-y",
            str(results_y),
            "--results-width",
            str(results_width),
            "--results-height",
            str(results_height),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return json.loads((completed.stdout or "{}").strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="QQ search state machine helper")
    parser.add_argument("--window-title", default="QQ")
    parser.add_argument("--contact", required=True)
    parser.add_argument("--search-x", type=int, default=200)
    parser.add_argument("--search-y", type=int, default=90)
    parser.add_argument("--results-x", type=int, default=0)
    parser.add_argument("--results-y", type=int, default=120)
    parser.add_argument("--results-width", type=int, default=420)
    parser.add_argument("--results-height", type=int, default=700)
    parser.add_argument("--pause-ms", type=int, default=500)
    args = parser.parse_args()

    steps: list[dict[str, Any]] = []

    focus_result = run_desktop(["focus-window-verified", args.window_title, "0", "false", "2", "250"])
    steps.append({"step": "focus_window_verified", "result": focus_result})
    time.sleep(max(0, args.pause_ms) / 1000.0)

    run_desktop(["mouse-move", str(args.search_x), str(args.search_y)])
    click_result = run_desktop(["mouse-click", "left"])
    steps.append({"step": "click_search_box", "result": click_result, "x": args.search_x, "y": args.search_y})
    time.sleep(max(0, args.pause_ms) / 1000.0)

    hotkey_result = run_desktop(["press-hotkey", "ctrl+a"])
    steps.append({"step": "select_all", "result": hotkey_result})
    time.sleep(0.15)

    backspace_result = run_desktop(["press-hotkey", "backspace"])
    steps.append({"step": "clear_search_text", "result": backspace_result})
    time.sleep(0.15)

    type_result = run_desktop(["type-text", args.contact])
    steps.append({"step": "type_contact", "result": type_result, "contact": args.contact})
    time.sleep(max(0, args.pause_ms) / 1000.0)

    helper_result = run_helper(
        args.contact,
        args.results_x,
        args.results_y,
        args.results_width,
        args.results_height,
    )
    steps.append({"step": "diagnose_results", "result": helper_result})

    output = {
        "ok": True,
        "windowTitle": args.window_title,
        "contact": args.contact,
        "targetFound": bool(helper_result.get("targetFound")),
        "steps": steps,
        "finalDiagnostic": helper_result,
    }
    sys.stdout.write(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
