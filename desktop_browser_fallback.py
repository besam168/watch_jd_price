from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILL_DIR = ROOT / "skills" / "telegram-image-sender"
CAPTURE_SCRIPT = SKILL_DIR / "scripts" / "capture-screen.ps1"
DESKTOP_OCR_SCRIPT = ROOT / "extensions" / "desktop-input-control" / "scripts" / "screen-ocr.py"
STATE_DIR = ROOT / "reports" / "scheduled"
STATE_DIR.mkdir(parents=True, exist_ok=True)


def run() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "missing_url"}, ensure_ascii=False))
        return 2

    url = sys.argv[1]
    wait_seconds = 4
    if len(sys.argv) >= 3:
        try:
            wait_seconds = max(1, int(sys.argv[2]))
        except Exception:
            pass

    result: dict[str, object] = {
        "ok": False,
        "url": url,
        "waitSeconds": wait_seconds,
        "browserOpened": False,
        "screenshotPath": None,
        "usedDesktopFallback": True,
        "ocrAvailable": False,
        "titleMatched": False,
        "ocrText": "",
    }

    try:
        subprocess.run([
            "python",
            "-c",
            f"import webbrowser; webbrowser.open({url!r})",
        ], cwd=str(ROOT), check=False, timeout=20)
        result["browserOpened"] = True
    except Exception as e:
        result["openError"] = str(e)

    time.sleep(wait_seconds)

    if CAPTURE_SCRIPT.exists():
        try:
            completed = subprocess.run(
                [
                    "powershell",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(CAPTURE_SCRIPT),
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                check=False,
            )
            stdout = (completed.stdout or "").strip()
            stderr = (completed.stderr or "").strip()
            result["captureReturnCode"] = completed.returncode
            result["captureStdout"] = stdout
            if stderr:
                result["captureStderr"] = stderr
            if stdout:
                last_line = stdout.splitlines()[-1].strip()
                if last_line.startswith("MEDIA:"):
                    result["screenshotPath"] = last_line.replace("MEDIA:", "", 1)
                elif ":\\" in last_line or last_line.endswith(".png"):
                    result["screenshotPath"] = last_line
        except Exception as e:
            result["captureError"] = str(e)

    expected_title = "bbc" if "bbc.com" in url.lower() else ""
    if result.get("screenshotPath") and DESKTOP_OCR_SCRIPT.exists():
        try:
            cmd = [
                "python",
                str(DESKTOP_OCR_SCRIPT),
                str(result["screenshotPath"]),
                "chi_sim+eng",
                "--preprocess",
                "gray_upscale2x",
            ]
            if expected_title:
                cmd.extend(["--query", expected_title, "--query-mode", "contains", "--top-n", "3"])
            ocr_completed = subprocess.run(
                cmd,
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=150,
                check=False,
            )
            payload = json.loads((ocr_completed.stdout or "{}").strip() or "{}")
            result["ocrAvailable"] = payload.get("ok", False) or ocr_completed.returncode == 0
            result["titleMatched"] = bool(payload.get("matches")) if isinstance(payload, dict) else False
            result["ocrText"] = (payload.get("text") or payload.get("fullText") or "")[:1000] if isinstance(payload, dict) else ""
            result["ocrReturnCode"] = ocr_completed.returncode
            if payload.get("error"):
                result["ocrError"] = payload.get("error")
            elif ocr_completed.stderr:
                result["ocrError"] = (ocr_completed.stderr or "")[:1000]
        except Exception as e:
            result["ocrError"] = str(e)

    result["ok"] = bool(result.get("browserOpened"))
    out_path = STATE_DIR / "desktop_browser_fallback.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(out_path))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
