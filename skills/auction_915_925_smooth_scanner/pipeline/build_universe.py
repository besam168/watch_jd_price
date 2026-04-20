import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
UNIVERSE_PATH = OUTPUT_DIR / "sz_mainboard_00_universe.json"


def code_ok(code: str) -> bool:
    if not code or len(code) != 6 or not code.isdigit():
        return False
    if not code.startswith("00"):
        return False
    if code.startswith(("300", "301", "688", "689", "8", "4")):
        return False
    return True


def classify_row(row: dict) -> tuple[bool, list[str]]:
    reasons = []
    code = str(row.get("code") or "")
    name = str(row.get("name") or "")
    days_since_list = row.get("days_since_list")
    security_type = str(row.get("security_type") or "stock")

    if not code_ok(code):
        reasons.append("not_sz_00_mainboard")
    if name.startswith(("N", "C")) or "退" in name:
        reasons.append("new_or_delisting_name_flag")
    if isinstance(days_since_list, int) and days_since_list < 60:
        reasons.append("listed_lt_60d")
    if security_type not in {"stock", "a_share", "common_stock", "unknown"}:
        reasons.append("non_common_security")
    return (len(reasons) == 0, reasons)


def build_universe(rows: list[dict]) -> dict:
    selected = []
    excluded = []
    for row in rows:
        ok, reasons = classify_row(row)
        item = dict(row)
        item["reasons"] = reasons
        if ok:
            selected.append(item)
        else:
            excluded.append(item)
    out = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "selected_count": len(selected),
        "excluded_count": len(excluded),
        "selected": selected,
        "excluded": excluded,
    }
    UNIVERSE_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


if __name__ == "__main__":
    sample = [
        {"code": "000001", "name": "平安银行", "days_since_list": 5000, "security_type": "stock"},
        {"code": "002001", "name": "新和成", "days_since_list": 5000, "security_type": "stock"},
        {"code": "300001", "name": "特锐德", "days_since_list": 5000, "security_type": "stock"},
        {"code": "001234", "name": "N测试股", "days_since_list": 10, "security_type": "stock"},
    ]
    result = build_universe(sample)
    print(json.dumps({"selected_count": result["selected_count"], "excluded_count": result["excluded_count"]}, ensure_ascii=False))
