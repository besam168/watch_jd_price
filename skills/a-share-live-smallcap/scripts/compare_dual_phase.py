#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / 'output'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

IN_0935 = OUTPUT_DIR / 'latest_0935_compare.json'
IN_0945 = OUTPUT_DIR / 'latest_0945_compare.json'
OUT_PATH = OUTPUT_DIR / 'dual_phase_compare_latest.json'


def index_by_code(items):
    out = {}
    for x in items or []:
        code = str(x.get('code') or '').strip()
        if code:
            out[code] = x
    return out


def merge_item(a, b):
    item = dict(a or {})
    item['phase_0935'] = a
    item['phase_0945'] = b
    item['code'] = (b or a).get('code')
    item['name'] = (b or a).get('name')
    item['change_pct_0935'] = (a or {}).get('change_pct')
    item['change_pct_0945'] = (b or {}).get('change_pct')
    item['track_score_0935'] = (a or {}).get('track_score')
    item['track_score_0945'] = (b or {}).get('track_score')
    item['intraday_score_0935'] = (a or {}).get('intraday_score')
    item['intraday_score_0945'] = (b or {}).get('intraday_score')
    return item


def brief(items):
    out = []
    for x in items:
        out.append({
            'code': x.get('code'),
            'name': x.get('name'),
            'change_pct_0935': x.get('change_pct_0935'),
            'change_pct_0945': x.get('change_pct_0945'),
            'track_score_0935': x.get('track_score_0935'),
            'track_score_0945': x.get('track_score_0945'),
        })
    return out


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    d35 = load_json(IN_0935)
    d45 = load_json(IN_0945)

    pool35 = index_by_code((d35.get('true_leaders') or []) + (d35.get('strong_followers') or []) + (d35.get('watchlist') or []))
    pool45 = index_by_code((d45.get('true_leaders') or []) + (d45.get('strong_followers') or []) + (d45.get('watchlist') or []))

    codes35 = set(pool35.keys())
    codes45 = set(pool45.keys())

    kept = [merge_item(pool35[c], pool45[c]) for c in sorted(codes35 & codes45)]
    new_at_0945 = [merge_item(None, pool45[c]) for c in sorted(codes45 - codes35)]
    dropped_after_0935 = [merge_item(pool35[c], None) for c in sorted(codes35 - codes45)]

    kept.sort(key=lambda x: ((x.get('track_score_0945') or 0), (x.get('change_pct_0945') or 0)), reverse=True)
    new_at_0945.sort(key=lambda x: ((x.get('track_score_0945') or 0), (x.get('change_pct_0945') or 0)), reverse=True)
    dropped_after_0935.sort(key=lambda x: ((x.get('track_score_0935') or 0), (x.get('change_pct_0935') or 0)), reverse=True)

    payload = {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'summary': {
            'phase_0935_pool': len(pool35),
            'phase_0945_pool': len(pool45),
            'kept_count': len(kept),
            'new_at_0945_count': len(new_at_0945),
            'dropped_after_0935_count': len(dropped_after_0935),
        },
        'kept': brief(kept),
        'new_at_0945': brief(new_at_0945),
        'dropped_after_0935': brief(dropped_after_0935),
    }
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
