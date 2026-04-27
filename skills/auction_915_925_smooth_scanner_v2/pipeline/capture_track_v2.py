from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
PIPELINE_DIR = BASE_DIR / 'pipeline'
DATASOURCE_DIR = BASE_DIR / 'datasource'
OUTPUT_DIR = BASE_DIR / 'outputs'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
UNIVERSE_PATH = Path(r'C:\Users\besam\.openclaw\workspace\skills\auction_915_925_smooth_scanner\outputs\liutong8yi_marketcap150yi_universe_full.json')
sys.path.insert(0, str(DATASOURCE_DIR))

from pytdx_snapshot import fetch_quotes_with_fallback  # type: ignore


def normalize_code(code: str) -> str:
    c = str(code or '').strip()
    if c.startswith(('sz', 'sh')):
        return c.lower()
    if c.startswith(('000', '001', '002', '003')):
        return 'sz' + c
    return 'sh' + c


def load_universe(limit: int = 0) -> list[dict]:
    obj = json.loads(UNIVERSE_PATH.read_text(encoding='utf-8'))
    rows = obj.get('selected') or []
    out = []
    for row in rows:
        code = str(row.get('code') or '').strip()
        if not code:
            continue
        out.append({'code': code, 'symbol': normalize_code(code), 'name': str(row.get('name') or code)})
    if limit and limit > 0:
        out = out[:limit]
    return out


def safe_float(value, default=0.0):
    try:
        if value is None or value == '':
            return default
        return float(value)
    except Exception:
        return default


def reference_price(row: dict) -> float:
    bid1 = safe_float(row.get('bid1'))
    ask1 = safe_float(row.get('ask1'))
    price = safe_float(row.get('price'))
    last_close = safe_float(row.get('last_close'))
    if bid1 > 0 and ask1 > 0:
        return round((bid1 + ask1) / 2, 4)
    if price > 0:
        return round(price, 4)
    if bid1 > 0:
        return round(bid1, 4)
    if ask1 > 0:
        return round(ask1, 4)
    if last_close > 0:
        return round(last_close, 4)
    return 0.0


def snapshot_one_round(universe: list[dict]) -> dict:
    symbols = [x['symbol'] for x in universe]
    result = fetch_quotes_with_fallback(symbols, primary_batch_size=5)
    quote_map = {}
    for row in result.get('rows') or []:
        code = str(row.get('code') or '').strip()
        if not code:
            continue
        quote_map[code] = row
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    round_rows = []
    for meta in universe:
        row = quote_map.get(meta['code']) or {}
        round_rows.append({
            'code': meta['code'],
            'symbol': meta['symbol'],
            'name': meta['name'],
            'captured_at': now,
            'price': reference_price(row),
            'last_close': safe_float(row.get('last_close')),
            'bid1': safe_float(row.get('bid1')),
            'ask1': safe_float(row.get('ask1')),
            'bid_vol1': safe_float(row.get('bid_vol1')),
            'ask_vol1': safe_float(row.get('ask_vol1')),
            'volume_ratio_proxy': round((safe_float(row.get('bid_vol1')) + safe_float(row.get('ask_vol1'))) / max(safe_float(row.get('last_close')) * 10.0, 1.0), 4),
            'servertime': row.get('servertime'),
        })
    return {'captured_at': now, 'stats': result.get('stats') or {}, 'rows': round_rows}


def main():
    limit = 0
    rounds = 6
    interval_seconds = 5
    out_path = OUTPUT_DIR / 'auction_sniper_v2_track_auto_today.json'
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
    if len(sys.argv) > 2:
        rounds = int(sys.argv[2])
    if len(sys.argv) > 3:
        interval_seconds = int(sys.argv[3])
    universe = load_universe(limit)
    payload = {
        'plugin': 'auction_915_925_smooth_scanner_v2',
        'mode': 'track_capture',
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'rounds': rounds,
        'interval_seconds': interval_seconds,
        'universe_size': len(universe),
        'round_payloads': [],
    }
    for i in range(rounds):
        payload['round_payloads'].append(snapshot_one_round(universe))
        if i < rounds - 1:
            time.sleep(interval_seconds)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'output': str(out_path), 'rounds': rounds, 'interval_seconds': interval_seconds, 'universe_size': len(universe)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
