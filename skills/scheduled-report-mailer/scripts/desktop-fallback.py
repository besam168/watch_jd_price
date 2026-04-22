from __future__ import annotations

import json
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = SKILL_ROOT / "config" / "report-config.json"
OUT_PATH = SKILL_ROOT / "state" / "desktop-fallback-status.json"


def main() -> int:
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    fallback_cfg = cfg.get("desktop_fallback", {})
    status = {
        "enabled": bool(fallback_cfg.get("enabled", False)),
        "mode": fallback_cfg.get("mode", "placeholder"),
        "status": "placeholder-only",
        "message": "Desktop fallback entry is wired into the pipeline but does not yet auto-browse pages.",
    }
    OUT_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(OUT_PATH))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
