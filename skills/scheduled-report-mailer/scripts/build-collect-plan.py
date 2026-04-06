from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = SKILL_ROOT / "config" / "report-config.json"
STATE_DIR = SKILL_ROOT / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    policy = cfg.get("collection_policy", {})
    out = {
        "generatedAt": datetime.now().isoformat(),
        "timeWindowHours": policy.get("time_window_hours", {"min": 0, "max": 24}),
        "mustCheck": policy.get("must_check", []),
        "sourceGroups": policy.get("source_groups", {}),
        "captureStrategies": policy.get("capture_strategies", []),
        "whitelistUrls": policy.get("whitelist_urls", []),
        "antiHallucination": policy.get("anti_hallucination", {}),
    }
    path = STATE_DIR / "collect-plan.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
