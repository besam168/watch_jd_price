#!/usr/bin/env python3
import argparse
import json
from datetime import datetime
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / 'outputs'
TRACK_PATH = OUTPUT_DIR / 'auction_sniper_v2_track_auto_today.json'
OUTPUT_MODULE_DIR = BASE_DIR / 'output'
sys.path.insert(0, str(OUTPUT_MODULE_DIR))
from writer import write_outputs  # type: ignore


def parse_args():
    p = argparse.ArgumentParser(description='使用连续竞价轨迹做 V2 模式判定')
    p.add_argument('--track-file', default=str(TRACK_PATH))
    p.add_argument('--top-n', type=int, default=30)
    p.add_argument('--json', action='store_true')
    return p.parse_args()


def safe_float(value, default=0.0):
    try:
        if value is None or value == '':
            return default
        return float(value)
    except Exception:
        return default


def mode_label(mode: str) -> str:
    if mode == 'sanan':
        return '三安模式'
    if mode == 'jinmantang':
        return '金螳螂模式'
    return '未入选'


def build_track_map(track_payload: dict) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for round_payload in track_payload.get('round_payloads') or []:
        for row in round_payload.get('rows') or []:
            code = str(row.get('code') or '').strip()
            if not code:
                continue
            out.setdefault(code, []).append(row)
    return out


def analyze_one(meta_rows: list[dict]) -> dict:
    first = meta_rows[0]
    code = str(first.get('code') or '')
    symbol = str(first.get('symbol') or code)
    name = str(first.get('name') or code)
    last_close = safe_float(first.get('last_close'))
    prices = [safe_float(x.get('price')) for x in meta_rows if safe_float(x.get('price')) > 0]
    vol_ratios = [safe_float(x.get('volume_ratio_proxy')) for x in meta_rows]
    if not prices or last_close <= 0:
        return {
            'mode': '', 'symbol': symbol, 'name': name, 'date': datetime.now().strftime('%Y%m%d'),
            'source': 'pytdx_snapshot_track', 'data_granularity': 'snapshot_polling_track',
            'price_092430': 0.0, 'price_0915_ref': last_close, 'price_0919_high': 0.0, 'price_0920_ref': 0.0,
            'change_pct': 0.0, 'volume_ratio': 0.0, 'passed': False, 'fail_reasons': 'track_or_last_close_missing',
            'note': '连续轨迹不足，无法判定',
        }

    current = prices[-1]
    peak = max(prices)
    trough = min(prices)
    volume_ratio = round(max(vol_ratios) if vol_ratios else 0.0, 4)
    change_pct = round((current - last_close) / last_close * 100.0, 4)
    peak_pct = round((peak - last_close) / last_close * 100.0, 4)
    drift_up = prices[-1] >= prices[0] and sum(1 for i in range(1, len(prices)) if prices[i] >= prices[i - 1]) >= max(1, len(prices) - 2)
    retrace_ok = peak > current and ((peak - current) / max(last_close, 0.01) * 100.0) >= 1.0

    mode = ''
    reasons = []
    if drift_up and 2.0 <= change_pct <= 5.0 and volume_ratio > 1.5:
        mode = 'sanan'
    elif peak_pct >= 9.0 and retrace_ok and 1.0 <= change_pct <= 5.0 and volume_ratio > 2.5:
        mode = 'jinmantang'
    else:
        if not drift_up:
            reasons.append('no_stable_lift_after_0920')
        if peak_pct < 9.0:
            reasons.append('no_limitup_touch_before_pullback')
        if not (1.0 <= change_pct <= 5.0 or 2.0 <= change_pct <= 5.0):
            reasons.append('change_pct_out_of_range')
        if volume_ratio <= 1.5:
            reasons.append('volume_ratio_too_low')

    return {
        'mode': mode,
        'symbol': symbol,
        'name': name,
        'date': datetime.now().strftime('%Y%m%d'),
        'source': 'pytdx_snapshot_track',
        'data_granularity': 'snapshot_polling_track',
        'price_092430': round(current, 4),
        'price_0915_ref': round(last_close, 4),
        'price_0919_high': round(peak, 4),
        'price_0920_ref': round(prices[0], 4),
        'change_pct': change_pct,
        'volume_ratio': volume_ratio,
        'passed': bool(mode),
        'fail_reasons': ';'.join(reasons),
        'note': f'基于连续采样轨迹判定：{mode_label(mode)}' if mode else '基于连续采样轨迹判定：未入选',
    }


def main():
    args = parse_args()
    track_path = Path(args.track_file)
    if not track_path.exists():
        raise SystemExit(f'track_file_not_found: {track_path}')
    payload = json.loads(track_path.read_text(encoding='utf-8'))
    track_map = build_track_map(payload)
    all_rows = [analyze_one(rows) for _, rows in track_map.items()]
    passed_rows = [x for x in all_rows if x.get('passed')]
    passed_rows.sort(key=lambda x: (x.get('change_pct') or 0, x.get('volume_ratio') or 0), reverse=True)
    passed_rows = passed_rows[:args.top_n]
    date_text = datetime.now().strftime('%Y%m%d')
    outputs = write_outputs(BASE_DIR, date_text, passed_rows, all_rows)
    result = {
        'plugin': 'auction_915_925_smooth_scanner_v2',
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'mode': 'track_judgement',
        'track_file': str(track_path),
        'passed_count': len(passed_rows),
        'outputs': outputs,
        'passed': passed_rows,
        'compact_lines': [f"[{'三安模式' if x.get('mode') == 'sanan' else '金螳螂模式'}] {x.get('symbol', '').upper()} - {x.get('name', '')} - {x.get('change_pct')}% - 量比{x.get('volume_ratio')}" for x in passed_rows],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.json else None))


if __name__ == '__main__':
    main()
