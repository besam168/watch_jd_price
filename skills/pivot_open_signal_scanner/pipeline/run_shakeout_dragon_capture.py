#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
import sys
from typing import Any
import urllib.request

BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE = Path(__file__).resolve().parents[3]
OUTPUT_DIR = BASE_DIR / 'outputs'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_JSON = OUTPUT_DIR / 'shakeout_dragon_capture.json'
OUTPUT_CSV = OUTPUT_DIR / 'shakeout_dragon_capture.csv'
OUTPUT_MD = OUTPUT_DIR / 'shakeout_dragon_capture.md'

UNIVERSE_PATH = Path(r'C:\Users\besam\.openclaw\workspace\skills\auction_915_925_smooth_scanner\outputs\liutong8yi_marketcap150yi_universe_full.json')
NAME_MAP_PATH = Path(r'C:\Users\besam\.openclaw\workspace\skills\auction_915_925_smooth_scanner_v2\references\name_map_v2.csv')
FALLBACK_NAME_MAP_PATH = Path(r'C:\Users\besam\.openclaw\workspace\skills\a-share-hot-spots\references\name_map.csv')
SHARED_POOL_DIR = WORKSPACE / 'skills' / 'shared_a_share_pool'
V2_DATASOURCE_DIR = Path(r'C:\Users\besam\.openclaw\workspace\skills\auction_915_925_smooth_scanner_v2\datasource')
sys.path.insert(0, str(V2_DATASOURCE_DIR))
sys.path.insert(0, str(SHARED_POOL_DIR.parent))
from pytdx_snapshot import fetch_quotes_with_fallback, TdxHq_API, market_for_code, DEFAULT_SERVERS  # type: ignore
from shared_a_share_pool import UniverseFilters, load_shared_universe, names_from_universe  # type: ignore


def _fetch_daily_bars_once(symbol: str, days: int, server: tuple[str, int]) -> list['DailyBar']:
    api = TdxHq_API()
    host, port = server
    code = symbol.replace('sz', '').replace('sh', '')
    market = market_for_code(code)
    try:
        ok = api.connect(host, port, time_out=1)
    except Exception:
        return []
    if not ok:
        return []
    try:
        rows = api.get_security_bars(9, market, code, 0, days) or []
        out: list[DailyBar] = []
        for row in rows:
            d = dict(row)
            out.append(DailyBar({
                'date': d.get('datetime') or d.get('date'),
                'open': safe_float(d.get('open')),
                'close': safe_float(d.get('close')),
                'high': safe_float(d.get('high')),
                'low': safe_float(d.get('low')),
                'vol': safe_float(d.get('vol') or d.get('volume')),
            }))
        return out
    except Exception:
        return []
    finally:
        try:
            api.disconnect()
        except Exception:
            pass


def load_daily_bars_with_fallback(symbol: str, days: int = 32) -> tuple[list['DailyBar'], dict[str, Any]]:
    stats: dict[str, Any] = {
        'symbol': symbol,
        'days': days,
        'servers_tried': [],
        'server_success': None,
    }
    for host, port in DEFAULT_SERVERS:
        stats['servers_tried'].append(f'{host}:{port}')
        bars = _fetch_daily_bars_once(symbol, days, (host, port))
        if bars:
            stats['server_success'] = f'{host}:{port}'
            return bars, stats
    return [], stats


class DailyBar(dict):
    @property
    def open(self) -> float:
        return float(self.get('open') or 0.0)

    @property
    def close(self) -> float:
        return float(self.get('close') or 0.0)

    @property
    def high(self) -> float:
        return float(self.get('high') or 0.0)

    @property
    def low(self) -> float:
        return float(self.get('low') or 0.0)

    @property
    def vol(self) -> float:
        return float(self.get('vol') or self.get('volume') or 0.0)


def _load_map_file(path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    if not path.exists():
        return mapping
    try:
        for line in path.read_text(encoding='utf-8-sig', errors='ignore').splitlines():
            parts = [x.strip() for x in line.split(',')]
            if len(parts) < 2:
                continue
            a, b = parts[0], parts[1]
            if a.lower() == 'name' and b.lower() == 'code':
                continue
            if a.isdigit() and len(a) == 6:
                mapping[a] = b
            elif b.isdigit() and len(b) == 6:
                mapping[b] = a
    except Exception:
        return mapping
    return mapping


def load_name_map() -> dict[str, str]:
    mapping = _load_map_file(NAME_MAP_PATH)
    fallback = _load_map_file(FALLBACK_NAME_MAP_PATH)
    for code, name in fallback.items():
        mapping.setdefault(code, name)
    return mapping


def _fetch_name_from_eastmoney(code: str) -> str:
    digits = ''.join(ch for ch in str(code or '') if ch.isdigit())
    if len(digits) != 6:
        return ''
    secid = ('1.' + digits) if digits.startswith(('5', '6', '9')) else ('0.' + digits)
    url = f'https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f57,f58'
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            raw = resp.read()
        obj = json.loads(raw.decode('utf-8'))
        data = obj.get('data') or {}
        name = str(data.get('f58') or '').strip()
        return name
    except Exception:
        return ''


def resolve_stock_name(code: str, raw_name: str = '') -> str:
    digits = ''.join(ch for ch in str(code or '') if ch.isdigit())
    candidates = [
        _fetch_name_from_eastmoney(digits),
        NAME_MAP.get(digits, ''),
        decode_name(raw_name),
        str(raw_name or '').strip(),
    ]
    for name in candidates:
        text = str(name or '').strip()
        if not text:
            continue
        if '\ufffd' in text:
            continue
        if all(ch == '?' for ch in text):
            continue
        return text
    return digits or str(code or '').strip()


NAME_MAP = load_name_map()


def normalize_code(code: str) -> str:
    c = str(code or '').strip()
    if c.startswith(('sz', 'sh')):
        return c.lower()
    if c.startswith(('000', '001', '002', '003')):
        return 'sz' + c
    return 'sh' + c


def safe_float(value, default=0.0):
    try:
        if value is None or value == '':
            return default
        return float(value)
    except Exception:
        return default


def decode_name(text: str) -> str:
    s = str(text or '')
    try:
        fixed = s.encode('latin1', errors='ignore').decode('gbk', errors='ignore')
        return fixed or s
    except Exception:
        return s


def load_universe(limit: int = 0) -> list[dict]:
    filters = UniverseFilters(
        allow_markets=('sz', 'sh'),
        include_prefixes=('00', '001', '002', '003', '600', '601', '603', '605'),
        exclude_prefixes=('300', '301', '688', '689', '8', '4'),
        exclude_st=True,
        exclude_delisting=True,
        min_listed_days=60,
        max_float_mkt_cap=150 * 1e8,
        max_liutongguben=8 * 1e8,
        limit=max(limit or 0, 3000) if limit else 3000,
    )
    universe_obj = load_shared_universe(universe_path=UNIVERSE_PATH, filters=filters)
    shared_names = names_from_universe(universe_obj)
    out = []
    for row in universe_obj.get('selected', []):
        code = str(row.get('code') or '').strip()
        if not code:
            continue
        resolved_name = resolve_stock_name(code, shared_names.get(code) or str(row.get('name') or code))
        out.append({'code': code, 'symbol': normalize_code(code), 'name': resolved_name})
    if limit and limit > 0:
        out = out[:limit]
    return out


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


def snapshot_universe(universe: list[dict]) -> list[dict]:
    result = fetch_quotes_with_fallback([x['symbol'] for x in universe], primary_batch_size=50)
    quote_map = {str(row.get('code') or '').strip(): row for row in (result.get('rows') or [])}
    rows = []
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for meta in universe:
        row = quote_map.get(meta['code']) or {}
        rows.append({
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
        })
    return rows


def load_daily_bars(symbol: str, days: int = 32) -> tuple[list[DailyBar], dict[str, Any]]:
    return load_daily_bars_with_fallback(symbol, days)


def is_limit_touch(bar: DailyBar, prev_close: float) -> bool:
    if prev_close <= 0:
        return False
    return bar.high >= round(prev_close * 1.095, 4)


def evaluate_history(bars: list[DailyBar], signal_offsets: tuple[int, ...], min_up_days: int, min_volume_multiple: float, post_days: int, post_vol_ratio_max: float, post_avg_vol_ratio_max: float, require_limit_touch: bool) -> dict[str, Any]:
    if len(bars) < 8:
        return {'passed': False, 'reason': 'not_enough_daily_bars'}
    bars = bars[-(max(signal_offsets) + post_days + 6):]
    latest_index = len(bars) - 1
    last_reason = 'no_valid_signal_day'
    for offset in signal_offsets:
        sig_idx = latest_index - offset
        if sig_idx - 5 < 0 or sig_idx + post_days >= len(bars):
            last_reason = 'signal_window_out_of_range'
            continue
        signal = bars[sig_idx]
        prev = bars[sig_idx - 1]
        window = bars[sig_idx - 5:sig_idx + 1]
        up_days = sum(1 for b in window if b.close > b.open)
        if up_days < min_up_days:
            last_reason = 'up_days_not_enough'
            continue
        if signal.vol < max(prev.vol * min_volume_multiple, 1.0):
            last_reason = 'signal_volume_not_enough'
            continue
        if signal.close <= signal.open:
            last_reason = 'signal_not_bullish'
            continue
        if require_limit_touch and not is_limit_touch(signal, prev.close):
            last_reason = 'limit_touch_not_met'
            continue
        base_price = signal.open
        post = bars[sig_idx + 1:sig_idx + 1 + post_days]
        if len(post) < post_days:
            last_reason = 'post_days_not_enough'
            continue
        if any(b.low < base_price for b in post):
            last_reason = 'base_price_broken'
            continue
        if any(b.vol >= signal.vol for b in post):
            last_reason = 'post_volume_not_lower'
            continue
        avg_post_vol = sum(b.vol for b in post) / post_days
        if avg_post_vol >= signal.vol * post_avg_vol_ratio_max:
            last_reason = 'post_avg_volume_too_high'
            continue
        if any((b.vol / signal.vol) > post_vol_ratio_max for b in post):
            last_reason = 'post_vol_ratio_too_high'
            continue
        return {
            'passed': True,
            'signal_offset': offset,
            'base_price': round(base_price, 4),
            'signal_volume': round(signal.vol, 4),
            'signal_open': round(signal.open, 4),
            'signal_close': round(signal.close, 4),
            'reason': 'shakeout_pattern_confirmed',
        }
    return {'passed': False, 'reason': last_reason}


def build_result_payload(candidates: list[dict], all_rows: list[dict], config: dict[str, Any]) -> dict:
    return {
        'plugin': 'shakeout_dragon_capture',
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'config': config,
        'passed_count': len(candidates),
        'candidates': candidates,
        'all_rows': all_rows,
    }


def write_outputs(payload: dict) -> None:
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    with OUTPUT_CSV.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['symbol', 'name', 'signal_offset', 'base_price', 'signal_volume', 'last_close', 'note'])
        writer.writeheader()
        for row in payload.get('candidates', []):
            writer.writerow({k: row.get(k) for k in ['symbol', 'name', 'signal_offset', 'base_price', 'signal_volume', 'last_close', 'note']})
    lines = [f"# Shakeout Dragon Capture\n", f"- generated_at: {payload['generated_at']}\n", f"- passed_count: {payload['passed_count']}\n", "\n## Candidates\n"]
    for row in payload.get('candidates', []):
        lines.append(f"- {row.get('symbol')} {row.get('name')} | offset={row.get('signal_offset')} | base={row.get('base_price')} | vol={row.get('signal_volume')} | note={row.get('note')}\n")
    OUTPUT_MD.write_text(''.join(lines), encoding='utf-8')


def main() -> None:
    p = argparse.ArgumentParser(description='Shakeout Dragon Capture')
    p.add_argument('--limit', type=int, default=300)
    p.add_argument('--signal-offsets', default='2,3,4')
    p.add_argument('--min-up-days', type=int, default=4)
    p.add_argument('--min-volume-multiple', type=float, default=2.0)
    p.add_argument('--post-days', type=int, default=3)
    p.add_argument('--post-vol-ratio-max', type=float, default=1.0)
    p.add_argument('--post-avg-vol-ratio-max', type=float, default=0.7)
    p.add_argument('--require-limit-touch', action='store_true')
    args = p.parse_args()

    signal_offsets = tuple(int(x.strip()) for x in args.signal_offsets.split(',') if x.strip())
    config = {
        'limit': args.limit,
        'signal_offsets': list(signal_offsets),
        'min_up_days': args.min_up_days,
        'min_volume_multiple': args.min_volume_multiple,
        'post_days': args.post_days,
        'post_vol_ratio_max': args.post_vol_ratio_max,
        'post_avg_vol_ratio_max': args.post_avg_vol_ratio_max,
        'require_limit_touch': args.require_limit_touch,
        'history_source': 'pytdx_daily_bars',
    }

    universe = load_universe(args.limit)
    snapshot_rows = snapshot_universe(universe)
    candidates = []
    reason_counts: dict[str, int] = {}
    failed_examples: list[dict[str, Any]] = []
    daily_bar_fetch_stats: list[dict[str, Any]] = []
    for meta in universe:
        bars, fetch_stats = load_daily_bars(meta['symbol'], 32)
        daily_bar_fetch_stats.append(fetch_stats)
        ev = evaluate_history(bars, signal_offsets, args.min_up_days, args.min_volume_multiple, args.post_days, args.post_vol_ratio_max, args.post_avg_vol_ratio_max, args.require_limit_touch) if bars else {'passed': False, 'reason': 'daily_bars_fetch_failed'}
        if ev.get('passed'):
            candidates.append({
                'symbol': meta['symbol'],
                'name': meta['name'],
                'signal_offset': ev.get('signal_offset'),
                'base_price': ev.get('base_price'),
                'signal_volume': ev.get('signal_volume'),
                'last_close': bars[-1].close if bars else 0.0,
                'note': '关注今日回踩或破位放量启动点',
                'reason': ev.get('reason'),
            })
        else:
            reason = str(ev.get('reason') or 'unknown')
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
            if len(failed_examples) < 15:
                failed_examples.append({'symbol': meta['symbol'], 'name': meta['name'], 'reason': reason})
    payload = build_result_payload(candidates, snapshot_rows, config)
    payload['reason_counts'] = reason_counts
    payload['daily_bar_fetch_stats'] = daily_bar_fetch_stats
    payload['failed_examples'] = failed_examples
    write_outputs(payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
