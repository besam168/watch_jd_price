#!/usr/bin/env python3
import argparse
import json
from datetime import datetime
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / 'outputs'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
UNIVERSE_PATH = Path(r'C:\Users\besam\.openclaw\workspace\skills\auction_915_925_smooth_scanner\outputs\liutong8yi_marketcap150yi_universe_full.json')
DATASOURCE_DIR = BASE_DIR / 'datasource'
OUTPUT_MODULE_DIR = BASE_DIR / 'output'
sys.path.insert(0, str(DATASOURCE_DIR))
sys.path.insert(0, str(OUTPUT_MODULE_DIR))

from pytdx_snapshot import fetch_quotes_with_fallback  # type: ignore
from writer import write_outputs  # type: ignore


def parse_args():
    p = argparse.ArgumentParser(description='集合竞价狙击手 V2')
    p.add_argument('--date', default='auto_today')
    p.add_argument('--limit', type=int, default=0)
    p.add_argument('--top-n', type=int, default=30)
    p.add_argument('--json', action='store_true')
    return p.parse_args()


def normalize_code(code: str) -> str:
    c = str(code or '').strip()
    if c.startswith(('sz', 'sh')):
        return c.lower()
    if c.startswith(('000', '001', '002', '003')):
        return 'sz' + c
    return 'sh' + c


def decode_name(text: str) -> str:
    s = str(text or '')
    try:
        fixed = s.encode('latin1', errors='ignore').decode('gbk', errors='ignore')
        return fixed or s
    except Exception:
        return s



def load_universe(limit: int = 0) -> list[dict]:
    if not UNIVERSE_PATH.exists():
        raise SystemExit(f'universe_not_found: {UNIVERSE_PATH}')
    obj = json.loads(UNIVERSE_PATH.read_text(encoding='utf-8'))
    rows = obj.get('selected') or []
    out = []
    for row in rows:
        code = str(row.get('code') or '').strip()
        if not code:
            continue
        raw_name = str(row.get('name') or code)
        out.append({
            'code': code,
            'symbol': normalize_code(code),
            'name': decode_name(raw_name),
            'estimated_liutong_marketcap': row.get('estimated_liutong_marketcap'),
        })
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


def estimate_volume_ratio(row: dict) -> float:
    bid_vol1 = safe_float(row.get('bid_vol1'))
    ask_vol1 = safe_float(row.get('ask_vol1'))
    last_close = safe_float(row.get('last_close'))
    depth = bid_vol1 + ask_vol1
    if depth <= 0:
        return 0.0
    base = max(last_close * 10.0, 1.0)
    return round(depth / base, 4)


def build_candidate(meta: dict, row: dict, date_text: str) -> dict:
    current = reference_price(row)
    last_close = safe_float(row.get('last_close'))
    change_pct = round(((current - last_close) / last_close * 100.0), 4) if current > 0 and last_close > 0 else 0.0
    volume_ratio = estimate_volume_ratio(row)
    bid1 = safe_float(row.get('bid1'))
    ask1 = safe_float(row.get('ask1'))
    price_0919_high = max(current, bid1, ask1)
    price_0920_ref = current
    price_0915_ref = last_close

    sanan_ok = 2.0 <= change_pct <= 5.0 and volume_ratio > 1.5 and current >= price_0920_ref
    jinmantang_peak_pct = round(((price_0919_high - last_close) / last_close * 100.0), 4) if last_close > 0 else 0.0
    jinmantang_ok = jinmantang_peak_pct >= 9.0 and 1.0 <= change_pct <= 5.0 and volume_ratio > 2.5

    mode = ''
    note = '当前版本基于 09:24:30 附近 pytdx 快照做近似判定；旧 smooth 规则已停用，仅保留三安模式/金螳螂模式。'
    reasons = []
    if sanan_ok:
        mode = 'sanan'
    elif jinmantang_ok:
        mode = 'jinmantang'
    else:
        if not (2.0 <= change_pct <= 5.0 or 1.0 <= change_pct <= 5.0):
            reasons.append('change_pct_out_of_range')
        if volume_ratio <= 1.5:
            reasons.append('volume_ratio_too_low')
        if jinmantang_peak_pct < 9.0:
            reasons.append('no_limitup_like_peak_before_0920')

    return {
        'mode': mode,
        'symbol': meta['symbol'],
        'name': meta['name'],
        'date': date_text,
        'source': 'pytdx_snapshot',
        'data_granularity': 'snapshot_polling_approx_092430',
        'price_092430': current,
        'price_0915_ref': price_0915_ref,
        'price_0919_high': round(price_0919_high, 4),
        'price_0920_ref': price_0920_ref,
        'change_pct': change_pct,
        'volume_ratio': volume_ratio,
        'passed': bool(mode),
        'fail_reasons': ';'.join(reasons),
        'note': note,
    }


def main():
    args = parse_args()
    date_text = datetime.now().strftime('%Y%m%d') if args.date == 'auto_today' else str(args.date).replace('-', '')
    universe = load_universe(args.limit)
    symbols = [x['symbol'] for x in universe]
    result = fetch_quotes_with_fallback(symbols, primary_batch_size=5)
    quote_map = {}
    for row in result.get('rows') or []:
        code = str(row.get('code') or '').strip()
        if code:
            quote_map[code] = row

    all_rows = []
    for meta in universe:
        row = quote_map.get(meta['code'])
        if not row:
            all_rows.append({
                'mode': '',
                'symbol': meta['symbol'],
                'name': meta['name'],
                'date': date_text,
                'source': 'pytdx_snapshot',
                'data_granularity': 'snapshot_polling_approx_092430',
                'price_092430': 0.0,
                'price_0915_ref': 0.0,
                'price_0919_high': 0.0,
                'price_0920_ref': 0.0,
                'change_pct': 0.0,
                'volume_ratio': 0.0,
                'score': 0.0,
                'passed': False,
                'fail_reasons': 'quote_missing',
                'note': '未拿到该票快照',
            })
            continue
        all_rows.append(build_candidate(meta, row, date_text))

    passed_rows = [x for x in all_rows if x.get('passed')]
    passed_rows.sort(key=lambda x: (x.get('score') or 0), reverse=True)
    passed_rows = passed_rows[:args.top_n]
    outputs = write_outputs(BASE_DIR, date_text, passed_rows, all_rows)

    payload = {
        'plugin': 'auction_915_925_smooth_scanner_v2',
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'universe_size': len(universe),
        'passed_count': len(passed_rows),
        'stats': result.get('stats') or {},
        'outputs': outputs,
        'passed': passed_rows,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2 if args.json else None))


if __name__ == '__main__':
    main()
