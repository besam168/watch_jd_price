from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = SKILL_ROOT / "config" / "report-config.json"
OUT_PATH = SKILL_ROOT / "state" / "desktop-fallback-status.json"
ROOT_FALLBACK_SCRIPT = ROOT / "desktop_browser_fallback.py"
LATEST_COLLECT_STATUS_PATH = ROOT / "reports" / "scheduled" / "latest_collect_status.json"

TARGET_DOMAINS = [
    "reuters.com",
    "apnews.com",
    "bbc.com",
    "aljazeera.com",
    "theguardian.com",
    "dw.com",
    "france24.com",
    "cnbc.com",
]


def load_dynamic_fallback_urls(default_urls: list[str]) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()

    def push(url: str) -> None:
        u = (url or "").strip()
        if not u or u in seen:
            return
        seen.add(u)
        urls.append(u)

    try:
        payload = json.loads(LATEST_COLLECT_STATUS_PATH.read_text(encoding="utf-8"))
    except Exception:
        payload = {}

    for result in payload.get("results", []):
        if result.get("group") != "full_whitelist_probe":
            continue
        for item in result.get("items", []):
            url = str(item.get("url") or "").strip()
            if not url:
                continue
            lowered = url.lower()
            if not any(domain in lowered for domain in TARGET_DOMAINS):
                continue
            ok = bool(item.get("ok"))
            status = int(item.get("status") or 0)
            error = str(item.get("error") or "").lower()
            if (not ok) or status >= 400 or "forbidden" in error or "httperror" in error:
                push(url)

    for url in default_urls:
        lowered = str(url).lower()
        if any(domain in lowered for domain in TARGET_DOMAINS):
            push(str(url))

    return urls


def main() -> int:
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    fallback_cfg = cfg.get("desktop_fallback", {})
    enabled = bool(fallback_cfg.get("enabled", False))
    mode = str(fallback_cfg.get("mode", "conditional_trigger") or "conditional_trigger")

    status: dict[str, object] = {
        "generatedAt": datetime.now().isoformat(),
        "enabled": enabled,
        "mode": mode,
        "status": "skipped",
        "reason": "disabled",
        "url": None,
        "urls": [],
        "rc": None,
        "stdout": "",
        "stderr": "",
        "runner": str(ROOT_FALLBACK_SCRIPT),
        "outputPath": None,
        "runs": [],
    }

    if not enabled:
        OUT_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        print(str(OUT_PATH))
        return 0

    python_exe = cfg.get("python", "python")
    default_urls = fallback_cfg.get("default_urls", []) if isinstance(fallback_cfg.get("default_urls", []), list) else []
    urls = load_dynamic_fallback_urls([str(x).strip() for x in default_urls if str(x).strip()])
    wait_seconds = int(fallback_cfg.get("wait_seconds", 3) or 3)

    if not ROOT_FALLBACK_SCRIPT.exists():
        status["status"] = "failed"
        status["reason"] = "runner_missing"
        OUT_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        print(str(OUT_PATH))
        return 1

    if not urls:
        status["status"] = "failed"
        status["reason"] = "missing_fallback_urls"
        OUT_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        print(str(OUT_PATH))
        return 1

    runs: list[dict[str, object]] = []
    overall_rc = 0
    final_output_path = None
    combined_stdout: list[str] = []
    combined_stderr: list[str] = []

    for url in urls:
        completed = subprocess.run(
            [python_exe, str(ROOT_FALLBACK_SCRIPT), url, str(wait_seconds)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        output_path = stdout.strip().splitlines()[-1].strip() if stdout.strip() else None
        if stdout.strip():
            combined_stdout.append(stdout.strip())
        if stderr.strip():
            combined_stderr.append(stderr.strip())
        if output_path:
            final_output_path = output_path
        if completed.returncode != 0:
            overall_rc = completed.returncode
        runs.append(
            {
                "url": url,
                "rc": completed.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "outputPath": output_path,
            }
        )

    status.update(
        {
            "status": "ok" if overall_rc == 0 else "failed",
            "reason": "executed",
            "url": urls[0],
            "urls": urls,
            "rc": overall_rc,
            "stdout": "\n\n".join(combined_stdout),
            "stderr": "\n\n".join(combined_stderr),
            "outputPath": final_output_path,
            "runs": runs,
        }
    )

    OUT_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(OUT_PATH))
    return overall_rc


if __name__ == "__main__":
    raise SystemExit(main())
