from __future__ import annotations

from typing import List, Sequence, Tuple

from pytdx.hq import TdxHq_API

DEFAULT_SERVERS: List[Tuple[str, int]] = [
    ("183.60.224.178", 7709),
    ("39.108.28.120", 7709),
    ("119.147.212.81", 7709),
]


def market_for_code(code: str) -> int:
    c = str(code).strip()
    if c.startswith(("00", "001", "002", "003", "30")):
        return 0
    return 1


def normalize_code(symbol: str) -> str:
    s = str(symbol).lower().strip()
    if s.startswith(("sz", "sh")):
        return s[2:]
    return s


def _fetch_quotes_once(symbols: Sequence[str], server: Tuple[str, int]) -> List[dict]:
    api = TdxHq_API()
    host, port = server
    try:
        ok = api.connect(host, port, time_out=1)
    except Exception:
        return []
    if not ok:
        return []
    try:
        req = [(market_for_code(normalize_code(s)), normalize_code(s)) for s in symbols]
        rows = api.get_security_quotes(req) or []
        return [dict(x) for x in rows]
    except Exception:
        return []
    finally:
        try:
            api.disconnect()
        except Exception:
            pass


def fetch_quotes(symbols: Sequence[str], server: Tuple[str, int] | None = None) -> List[dict]:
    if server is not None:
        return _fetch_quotes_once(symbols, server)
    for srv in DEFAULT_SERVERS:
        rows = _fetch_quotes_once(symbols, srv)
        if rows:
            return rows
    return []


def fetch_quotes_with_fallback(symbols: Sequence[str], primary_batch_size: int = 5) -> dict:
    symbols = [normalize_code(x) for x in symbols]
    all_rows: List[dict] = []
    stats = {
        "requested": len(symbols),
        "batch_size": primary_batch_size,
        "primary_ok_batches": 0,
        "fallback_server_batches": 0,
        "fallback_single_ok": 0,
        "failed_symbols": [],
    }

    for i in range(0, len(symbols), primary_batch_size):
        batch = symbols[i:i + primary_batch_size]
        rows = _fetch_quotes_once(batch, DEFAULT_SERVERS[0])
        if rows:
            all_rows.extend(rows)
            stats["primary_ok_batches"] += 1
            continue

        got = []
        for srv in DEFAULT_SERVERS[1:]:
            rows = _fetch_quotes_once(batch, srv)
            if rows:
                got = rows
                stats["fallback_server_batches"] += 1
                break
        if got:
            all_rows.extend(got)
            continue

        for code in batch:
            single_rows = []
            for srv in DEFAULT_SERVERS:
                single_rows = _fetch_quotes_once([code], srv)
                if single_rows:
                    stats["fallback_single_ok"] += 1
                    break
            if single_rows:
                all_rows.extend(single_rows)
            else:
                stats["failed_symbols"].append(code)

    stats["returned"] = len(all_rows)
    stats["success_ratio"] = round(len(all_rows) / len(symbols), 4) if symbols else 0
    return {"rows": all_rows, "stats": stats}
