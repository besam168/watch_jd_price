from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "reports" / "scheduled" / "qveris_market_snapshot.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

TIMEOUT_SECONDS = 18
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OpenClaw/1.0",
    "Referer": "https://finance.sina.com.cn",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def _safe_float(v):
    try:
        if v is None:
            return None
        return float(str(v).replace(",", "").strip())
    except Exception:
        return None


def _as_quote(price=None, open_=None, low=None, high=None, dp=None) -> dict[str, float]:
    out: dict[str, float] = {}
    p = _safe_float(price)
    o = _safe_float(open_)
    l = _safe_float(low)
    h = _safe_float(high)
    d = _safe_float(dp)
    if p is not None:
        out["price"] = p
        out["c"] = p
    if o is not None:
        out["open"] = o
        out["o"] = o
    if l is not None:
        out["dayLow"] = l
        out["l"] = l
    if h is not None:
        out["dayHigh"] = h
        out["h"] = h
    if d is not None:
        out["dp"] = d
    return out


def _fetch_text(url: str, headers: dict[str, str] | None = None, decode: str = "utf-8") -> str:
    req = urllib.request.Request(url, headers=headers or HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        raw = resp.read()
    return raw.decode(decode, errors="replace")


def _fetch_json(url: str, headers: dict[str, str] | None = None) -> dict:
    text = _fetch_text(url, headers=headers, decode="utf-8")
    return json.loads(text)


def _set_if_missing(result: dict[str, object], key: str, quote: dict[str, object] | None) -> None:
    if key in result:
        return
    if not isinstance(quote, dict):
        return
    if quote.get("price") is None and quote.get("c") is None:
        return
    result[key] = quote


def _fetch_eastmoney_global_indices() -> dict[str, dict[str, object]]:
    secids = {
        "DJIA": "DJI",
        "NDX": "IXIC",
        "SPX": "SPX",
        "FTSE": "FTSE",
        "N225": "N225",
        "HSI": "HSI",
        "TWII": "TWII",
        "KS11": "KOSPI",
    }
    url = (
        "https://push2.eastmoney.com/api/qt/ulist.np/get"
        "?ut=bd1d9ddb04089700cf9c27f6f7426281"
        "&fltt=2&invt=2"
        "&fields=f12,f14,f2,f3,f4,f13"
        f"&secids={','.join(f'100.{x}' for x in secids.keys())}"
    )
    out: dict[str, dict[str, object]] = {}
    try:
        obj = _fetch_json(url, headers={**HEADERS, "Referer": "https://quote.eastmoney.com"})
        diff = (((obj or {}).get("data") or {}).get("diff") or [])
    except Exception:
        return out

    for row in diff:
        code = str(row.get("f12") or "").strip().upper()
        alias = secids.get(code)
        if not alias:
            continue
        quote = _as_quote(price=row.get("f2"), dp=row.get("f3"))
        if quote:
            quote["source"] = "eastmoney"
            out[alias] = quote
    return out


def _fetch_sina_indices_and_commodities() -> dict[str, dict[str, object]]:
    symbol_map = {
        "int_sp500": "SPX",
        "int_nasdaq": "IXIC",
        "int_dji": "DJI",
        "int_ftse": "FTSE",
        "int_nikkei": "N225",
        "int_hangseng": "HSI",
        "hf_GC": "XAUUSD",
        "hf_OIL": "BZUSD",
        "hf_CL": "CLUSD",
    }
    out: dict[str, dict[str, object]] = {}
    try:
        q = ",".join(symbol_map.keys())
        raw = _fetch_text(f"http://hq.sinajs.cn/list={q}", headers=HEADERS, decode="gbk")
    except Exception:
        return out

    for symbol, alias in symbol_map.items():
        m = re.search(rf'hq_str_{re.escape(symbol)}="([^"]*)"', raw)
        if not m:
            continue
        parts = m.group(1).split(",")
        if symbol.startswith("int_") and len(parts) >= 4:
            price = _safe_float(parts[1])
            dp = _safe_float(parts[3])
            quote = _as_quote(price=price, dp=dp)
            if quote:
                quote["source"] = "sina"
                out[alias] = quote
        elif symbol.startswith("hf_") and len(parts) >= 6:
            price = _safe_float(parts[0])
            high = _safe_float(parts[4])
            low = _safe_float(parts[5])
            open_ = _safe_float(parts[7]) if len(parts) > 7 else None
            prev_close = _safe_float(parts[8]) if len(parts) > 8 else None
            dp = None
            if price is not None and prev_close not in (None, 0.0):
                dp = (price - prev_close) / prev_close * 100
            quote = _as_quote(price=price, open_=open_, low=low, high=high, dp=dp)
            if quote:
                quote["source"] = "sina"
                out[alias] = quote
    return out


def _parse_tencent_quote_line(raw: str, symbol: str) -> dict[str, float] | None:
    m = re.search(rf'v_{re.escape(symbol)}="([^"]*)"', raw)
    if not m:
        return None
    parts = m.group(1).split("~")
    if len(parts) < 6:
        return None

    price = _safe_float(parts[3] if len(parts) > 3 else None)
    prev_close = _safe_float(parts[4] if len(parts) > 4 else None)
    open_ = _safe_float(parts[5] if len(parts) > 5 else None)

    dp = _safe_float(parts[32] if len(parts) > 32 else None)
    if dp is None and price is not None and prev_close not in (None, 0.0):
        dp = (price - prev_close) / prev_close * 100

    high = _safe_float(parts[33] if len(parts) > 33 else None)
    low = _safe_float(parts[34] if len(parts) > 34 else None)

    return _as_quote(price=price, open_=open_, low=low, high=high, dp=dp)


def _fetch_tencent_quotes() -> dict[str, dict[str, object]]:
    symbol_map = {
        "usDJI": "DJI",
        "usIXIC": "IXIC",
        "usINX": "SPX",
        "hkHSI": "HSI",
        "usAAPL": "AAPL",
        "usNVDA": "NVDA",
        "usTSLA": "TSLA",
    }
    out: dict[str, dict[str, object]] = {}
    try:
        q = ",".join(symbol_map.keys())
        raw = _fetch_text(
            f"https://qt.gtimg.cn/q={q}",
            headers={
                "User-Agent": HEADERS["User-Agent"],
                "Referer": "https://gu.qq.com",
                "Accept-Language": HEADERS["Accept-Language"],
            },
            decode="gbk",
        )
    except Exception:
        return out

    for symbol, alias in symbol_map.items():
        quote = _parse_tencent_quote_line(raw, symbol)
        if quote:
            quote["source"] = "tencent"
            out[alias] = quote
    return out


result: dict[str, object] = {}

# 1) 东方财富：优先覆盖全球指数（含TWII/KOSPI）
for k, v in _fetch_eastmoney_global_indices().items():
    _set_if_missing(result, k, v)

# 2) 新浪：补齐指数与商品（黄金/原油）
for k, v in _fetch_sina_indices_and_commodities().items():
    _set_if_missing(result, k, v)

# 3) 腾讯：补齐美股科技龙头与剩余指数
for k, v in _fetch_tencent_quotes().items():
    _set_if_missing(result, k, v)

OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(str(OUT))
print(f"market_snapshot_keys={len(result)}")
