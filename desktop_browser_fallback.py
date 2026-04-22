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
SCROLL_SCRIPT = ROOT / "desktop_browser_scroll.py"
STATE_DIR = ROOT / "reports" / "scheduled"
STATE_DIR.mkdir(parents=True, exist_ok=True)


def capture_once() -> tuple[str | None, dict]:
    meta: dict[str, object] = {}
    if not CAPTURE_SCRIPT.exists():
        return None, meta
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
        meta["returnCode"] = completed.returncode
        meta["stdout"] = stdout
        if stderr:
            meta["stderr"] = stderr
        shot = None
        if stdout:
            last_line = stdout.splitlines()[-1].strip()
            if last_line.startswith("MEDIA:"):
                shot = last_line.replace("MEDIA:", "", 1)
            elif ":\\" in last_line or last_line.endswith(".png"):
                shot = last_line
        return shot, meta
    except Exception as e:
        meta["error"] = str(e)
        return None, meta


def run_ocr(image_path: str, expected_title: str) -> dict:
    if not image_path or not DESKTOP_OCR_SCRIPT.exists():
        return {"ocrAvailable": False, "titleMatched": False, "ocrText": ""}
    try:
        cmd = [
            "python",
            str(DESKTOP_OCR_SCRIPT),
            str(image_path),
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
        return {
            "ocrAvailable": payload.get("ok", False) or ocr_completed.returncode == 0,
            "titleMatched": bool(payload.get("matches")) if isinstance(payload, dict) else False,
            "ocrText": (payload.get("text") or payload.get("fullText") or "")[:1000] if isinstance(payload, dict) else "",
            "ocrReturnCode": ocr_completed.returncode,
            "ocrError": payload.get("error") if isinstance(payload, dict) else "",
        }
    except Exception as e:
        return {"ocrAvailable": False, "titleMatched": False, "ocrText": "", "ocrError": str(e)}


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
        "screenshotPathTop": None,
        "screenshotPathScrolled": None,
        "usedDesktopFallback": True,
        "ocrAvailable": False,
        "titleMatched": False,
        "ocrText": "",
        "ocrTop": {},
        "ocrScrolled": {},
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

    shot_top, meta_top = capture_once()
    result["captureTop"] = meta_top
    if shot_top:
        result["screenshotPathTop"] = shot_top
        result["screenshotPath"] = shot_top

    if SCROLL_SCRIPT.exists():
        try:
            subprocess.run(["python", str(SCROLL_SCRIPT)], cwd=str(ROOT), check=False, timeout=30)
            time.sleep(2)
        except Exception as e:
            result["scrollError"] = str(e)

    shot_scrolled, meta_scrolled = capture_once()
    result["captureScrolled"] = meta_scrolled
    if shot_scrolled:
        result["screenshotPathScrolled"] = shot_scrolled

    expected_title = "bbc" if "bbc.com" in url.lower() else ""
    if result.get("screenshotPathTop"):
        ocr_top = run_ocr(str(result["screenshotPathTop"]), expected_title)
        result["ocrTop"] = ocr_top
    if result.get("screenshotPathScrolled"):
        ocr_scrolled = run_ocr(str(result["screenshotPathScrolled"]), expected_title)
        result["ocrScrolled"] = ocr_scrolled

    top_ok = isinstance(result.get("ocrTop"), dict) and bool(result["ocrTop"].get("ocrAvailable"))
    scrolled_ok = isinstance(result.get("ocrScrolled"), dict) and bool(result["ocrScrolled"].get("ocrAvailable"))
    result["ocrAvailable"] = bool(top_ok or scrolled_ok)
    result["titleMatched"] = bool((result.get("ocrTop") or {}).get("titleMatched") or (result.get("ocrScrolled") or {}).get("titleMatched"))
    result["ocrText"] = ((result.get("ocrTop") or {}).get("ocrText") or "") + "\n---SCROLLED---\n" + ((result.get("ocrScrolled") or {}).get("ocrText") or "")

    result["ok"] = bool(result.get("browserOpened"))
    out_path = STATE_DIR / "desktop_browser_fallback.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(out_path))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
