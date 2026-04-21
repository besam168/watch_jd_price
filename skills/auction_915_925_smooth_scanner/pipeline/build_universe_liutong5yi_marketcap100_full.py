import json
import time
from datetime import datetime
from pathlib import Path

from pytdx.hq import TdxHq_API

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUTPUT_DIR / "liutong5yi_marketcap100yi_universe_full.json"

SERVERS = [
    ("183.60.224.178", 7709),
    ("39.108.28.120", 7709),
    ("119.147.212.81", 7709),
]

LIUTONG_LIMIT = 500_000_000
MARKETCAP_LIMIT = 10_000_000_000


def connect_api():
    api = TdxHq_API()
    for host, port in SERVERS:
        try:
            ok = api.connect(host, port, time_out=1)
            if ok:
                return api
        except Exception:
            pass
    return None


def decode_name(text: str) -> str:
    s = str(text or "")
    try:
        return s.encode("latin1", errors="ignore").decode("gbk", errors="ignore") or s
    except Exception:
        return s


def board_ok(code: str) -> bool:
    if not code or len(code) != 6 or not code.isdigit():
        return False
    if code.startswith(("688", "689", "4", "8")):
        return False
    return code.startswith(("000", "001", "002", "003", "600", "601", "603", "605"))


def market_for_code(code: str) -> int:
    if code.startswith(("000", "001", "002", "003")):
        return 0
    return 1


def fetch_all_codes(api, market: int) -> list[dict]:
    total = api.get_security_count(market)
    rows = []
    step = 1000
    for start in range(0, total, step):
        part = api.get_security_list(market, start) or []
        for item in part:
            d = dict(item)
            code = str(d.get("code") or "")
            name = decode_name(str(d.get("name") or ""))
            if board_ok(code):
                rows.append({"code": code, "name": name, "market": market})
    return rows


def batch_quotes(api, codes: list[str]) -> dict[str, dict]:
    out = {}
    for i in range(0, len(codes), 5):
        batch = codes[i:i + 5]
        try:
            rows = api.get_security_quotes([(market_for_code(c), c) for c in batch]) or []
        except Exception:
            rows = []
        for row in rows:
            d = dict(row)
            code = str(d.get("code") or "")
            if code:
                out[code] = d
    return out


def fetch_finance(api, code: str) -> dict:
    try:
        return dict(api.get_finance_info(market_for_code(code), code) or {})
    except Exception:
        return {}


def latest_price_from_quote(q: dict) -> float | None:
    for key in ["price", "last_close", "bid1", "ask1"]:
        try:
            value = float(q.get(key))
        except Exception:
            value = None
        if value and value > 0:
            return value
    return None


def classify(row: dict) -> tuple[bool, list[str]]:
    reasons = []
    code = row.get("code", "")
    name = str(row.get("name") or code)
    upper_name = name.upper()
    liutongguben = row.get("liutongguben")
    est_marketcap = row.get("estimated_liutong_marketcap")
    ipo_date = row.get("ipo_date")

    if not board_ok(code):
        reasons.append("board_filtered")
    if upper_name.startswith(("N", "C")) or "退" in name:
        reasons.append("new_or_delisting_name_flag")
    if "ST" in upper_name:
        reasons.append("st_flag")
    if not liutongguben or liutongguben <= 0:
        reasons.append("invalid_liutongguben")
    if isinstance(liutongguben, (int, float)) and liutongguben > LIUTONG_LIMIT:
        reasons.append("liutongguben_gt_5yi_shares")
    if est_marketcap is None or est_marketcap <= 0:
        reasons.append("marketcap_missing")
    elif est_marketcap > MARKETCAP_LIMIT:
        reasons.append("float_mkt_cap_gt_100yi")
    if isinstance(ipo_date, int) and len(str(ipo_date)) == 8:
        dt = datetime.strptime(str(ipo_date), "%Y%m%d")
        if (datetime.now() - dt).days < 60:
            reasons.append("listed_lt_60d")
    return (len(reasons) == 0, reasons)


def main():
    api = connect_api()
    if not api:
        raise SystemExit("tdx_connect_failed")
    started = time.time()
    seeds = fetch_all_codes(api, 0) + fetch_all_codes(api, 1)
    unique = {}
    for row in seeds:
        unique[row["code"]] = row
    seeds = list(unique.values())
    quotes = batch_quotes(api, [row["code"] for row in seeds])

    selected = []
    excluded = []
    for row in seeds:
        code = row["code"]
        fin = fetch_finance(api, code)
        liutongguben = fin.get("liutongguben")
        try:
            liutongguben = float(liutongguben)
        except Exception:
            liutongguben = None
        latest = latest_price_from_quote(quotes.get(code, {}))
        est_marketcap = liutongguben * latest if liutongguben and latest else None
        item = {
            "code": code,
            "name": row.get("name"),
            "market": row.get("market"),
            "latest_price": round(latest, 4) if latest else None,
            "liutongguben": liutongguben,
            "estimated_liutong_marketcap": round(est_marketcap, 2) if est_marketcap else None,
            "ipo_date": fin.get("ipo_date"),
        }
        ok, reasons = classify(item)
        item["reasons"] = reasons
        if ok:
            selected.append(item)
        else:
            excluded.append(item)

    api.disconnect()
    elapsed = round(time.time() - started, 2)
    selected.sort(key=lambda x: x.get("estimated_liutong_marketcap") or 0, reverse=True)
    out = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "liutong_limit": LIUTONG_LIMIT,
        "marketcap_limit": MARKETCAP_LIMIT,
        "seed_count": len(seeds),
        "selected_count": len(selected),
        "excluded_count": len(excluded),
        "elapsed_seconds": elapsed,
        "selected": selected,
        "excluded": excluded,
    }
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "output": str(OUT_PATH),
        "seed_count": len(seeds),
        "selected_count": len(selected),
        "excluded_count": len(excluded),
        "elapsed_seconds": elapsed,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
