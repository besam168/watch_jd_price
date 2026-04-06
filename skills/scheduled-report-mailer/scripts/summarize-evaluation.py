from __future__ import annotations

import json
from pathlib import Path

STATE = Path(__file__).resolve().parents[1] / "state"
EVAL_PATH = STATE / "report-evaluation.json"
OUT_PATH = STATE / "report-evaluation-summary.txt"


def main() -> int:
    data = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    checks = data.get("mustCheckResults", {})
    missing = [k for k, v in checks.items() if not v.get("ok")]
    ok_count = data.get("summary", {}).get("okCount", 0)
    total = data.get("summary", {}).get("total", 0)
    if not missing:
        status = "通过"
        advice = "可直接发送，无需补抓。"
    elif ok_count >= max(total - 1, 1):
        status = "部分通过"
        advice = f"建议优先补抓：{', '.join(missing)}；如时效优先，也可先发后补。"
    else:
        status = "未通过"
        advice = f"建议重跑并补抓：{', '.join(missing)}。"
    text = "\n".join([
        f"状态：{status}",
        f"命中：{ok_count}/{total}",
        f"缺口：{', '.join(missing) if missing else '无'}",
        f"建议：{advice}",
    ])
    OUT_PATH.write_text(text, encoding="utf-8")
    print(str(OUT_PATH))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
