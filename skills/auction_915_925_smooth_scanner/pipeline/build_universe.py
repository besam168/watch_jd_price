import json
from datetime import datetime
from pathlib import Path

import akshare as ak

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


def decode_mojibake(text: str) -> str:
    if not text:
        return text
    try:
        return text.encode("latin1", errors="ignore").decode("gbk", errors="ignore") or text
    except Exception:
        return text


def parse_individual_info(df) -> dict:
    out = {}
    for _, row in df.iterrows():
        key = decode_mojibake(str(row.iloc[0]))
        value = row.iloc[1]
        out[key] = value
    return out


def fetch_base_codes() -> list[dict]:
    path = BASE_DIR.parent / "a-share-hot-spots" / "references" / "name_map.csv"
    rows = []
    if path.exists():
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            line = line.strip()
            if not line or "," not in line:
                continue
            parts = [x.strip() for x in line.split(",", 1)]
            if len(parts) < 2:
                continue
            name, code = parts[0], parts[1]
            if code_ok(code):
                rows.append({"code": code, "name": decode_mojibake(name)})
    return rows


def fetch_live_universe_rows(limit: int | None = None) -> list[dict]:
    base_rows = fetch_base_codes()
    rows = []
    count = 0
    for item in base_rows:
        code = str(item["code"]).zfill(6)
        name = decode_mojibake(str(item["name"]))
        days_since_list = None
        float_mkt_cap = None
        security_type = "stock"
        try:
            info_df = ak.stock_individual_info_em(symbol=code)
            info = parse_individual_info(info_df)
            listing_date = str(info.get("上市时间") or "").strip()
            if listing_date and listing_date.isdigit() and len(listing_date) == 8:
                dt = datetime.strptime(listing_date, "%Y%m%d")
                days_since_list = (datetime.now() - dt).days
            float_mkt_cap = info.get("流通市值")
        except Exception:
            pass
        rows.append({
            "code": code,
            "name": name,
            "days_since_list": days_since_list,
            "security_type": security_type,
            "float_mkt_cap": float_mkt_cap,
        })
        count += 1
        if limit and count >= limit:
            break
    return rows


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
    rows = fetch_live_universe_rows(limit=30)
    result = build_universe(rows)
    print(json.dumps({"selected_count": result["selected_count"], "excluded_count": result["excluded_count"]}, ensure_ascii=False))
