#!/usr/bin/env python3
import argparse
import json
import sys
import re
from pathlib import Path

import pandas as pd

PLUGIN_NAME = 'A股盘中中小盘强势股插件'
WORKSPACE = Path(__file__).resolve().parents[3]
HOT_SCRIPT = WORKSPACE / 'skills' / 'a-share-hot-spots' / 'scripts'
V6_TEST_SCRIPT = WORKSPACE / 'skills' / 'a-share-opening-flow-v6-test' / 'scripts'
sys.path.insert(0, str(HOT_SCRIPT))
sys.path.insert(0, str(V6_TEST_SCRIPT))

import market_watch as mw  # type: ignore
import opening_flow_v6_test as v6  # type: ignore


def load_code_name_map() -> dict:
    path = WORKSPACE / 'skills' / 'a-share-hot-spots' / 'references' / 'name_map.csv'
    mapping = {}
    if not path.exists():
        return mapping
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip() or ',' not in line:
            continue
        name, code = line.split(',', 1)
        mapping[code.strip()] = name.strip()
    return mapping


CODE_NAME_MAP = load_code_name_map()
LARGE_CAP_CODES = {
    '600519','300750','000858','600036','600030','300059','002594','601318','601012','601138',
    '688981','688256','601899','601888','000651','000333','603259','002475','688041','300308',
    '000977','002230','603019','600900','601127','601919','601336','600031','002241','002714',
    '600438','603501','002371','603986','002463','600019','601857','601088','000001','000002'
}
SMALLCAP_PREFERRED_PREFIX = ('300', '301', '688', '002', '003')


def normalize_name(text: str) -> str:
    if not text:
        return text
    try:
        fixed = mw._decode_possible_garbled(text)
        return fixed or text
    except Exception:
        return text


def try_fetch_live_market(top_n: int) -> tuple[list, str]:
    urls = [
        (
            f'http://push2.eastmoney.com/api/qt/clist/get?pn=1&pz={top_n}&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281'
            '&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14,f2,f3,f4,f5,f6,f20,f21'
        ),
        (
            f'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz={top_n}&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281'
            '&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14,f2,f3,f4,f5,f6,f20,f21'
        ),
    ]
    for url in urls:
        try:
            raw = mw.fetch_text(url, referer='https://quote.eastmoney.com')
            obj = json.loads(raw)
            diff = ((obj.get('data') or {}).get('diff') or [])
            out = []
            for item in diff:
                code = str(item.get('f12', '')).strip()
                if not re.fullmatch(r'\d{6}', code):
                    continue
                market = 'sh' if code.startswith(('60', '68')) else 'sz'
                name = normalize_name(str(item.get('f14', '')).strip()) or CODE_NAME_MAP.get(code, code)
                out.append({
                    'symbol': f'{market}{code}',
                    'code': code,
                    'name': name,
                    'current': round(mw.safe_float(item.get('f2', 0)), 2),
                    'change_pct': round(mw.safe_float(item.get('f3', 0)), 2),
                    'change': round(mw.safe_float(item.get('f4', 0)), 2),
                    'volume_lot': int(mw.safe_float(item.get('f5', 0))),
                    'amount_yi': round(mw.safe_float(item.get('f6', 0)) / 1e8, 2),
                    'total_mv_yi': round(mw.safe_float(item.get('f20', 0)) / 1e8, 2),
                    'circ_mv_yi': round(mw.safe_float(item.get('f21', 0)) / 1e8, 2),
                    'source': '东方财富实时全市场',
                })
            if out:
                out.sort(key=lambda x: (x.get('change_pct', 0), x.get('amount_yi', 0)), reverse=True)
                return out, 'eastmoney-live'
        except Exception:
            continue
    items = mw.fetch_hot_stocks()
    out = []
    for item in items:
        code = str(item.get('symbol', ''))[-6:]
        out.append({
            'symbol': item.get('symbol', ''),
            'code': code,
            'name': normalize_name(str(item.get('name', '')).strip()) or CODE_NAME_MAP.get(code, code),
            'current': round(mw.safe_float(item.get('current', 0)), 2),
            'change_pct': round(mw.safe_float(item.get('change_pct', 0)), 2),
            'change': round(mw.safe_float(item.get('change', 0)), 2),
            'volume_lot': int(mw.safe_float(item.get('volume_lot', 0))),
            'amount_yi': round(mw.safe_float(item.get('amount_yi', 0)), 2),
            'total_mv_yi': 0.0,
            'circ_mv_yi': 0.0,
            'source': item.get('source', '新浪/腾讯候选池fallback'),
        })
    out.sort(key=lambda x: (x.get('change_pct', 0), x.get('amount_yi', 0)), reverse=True)
    return out[:top_n], 'fallback-hot-stocks'


def infer_style(item: dict) -> list[str]:
    code = item.get('code', '')
    tags = []
    if code.startswith('301'):
        tags += ['创业板', '次新']
    elif code.startswith('300'):
        tags += ['创业板', '弹性票']
    elif code.startswith('688'):
        tags += ['科创板', '弹性票']
    elif code.startswith(('002', '003')):
        tags += ['中小盘主板']
    elif code.startswith('60'):
        tags += ['主板']
    return tags


def is_smallcap_style(item: dict) -> bool:
    code = item.get('code', '')
    total_mv = mw.safe_float(item.get('total_mv_yi', 0))
    circ_mv = mw.safe_float(item.get('circ_mv_yi', 0))
    if code in LARGE_CAP_CODES:
        return False
    if code.startswith(SMALLCAP_PREFERRED_PREFIX):
        return True
    if total_mv > 0 and total_mv <= 1200 and circ_mv <= 800:
        return True
    if code.startswith('60') and total_mv > 0 and total_mv > 1500:
        return False
    return code.startswith(('002', '003', '605', '603'))


def first_round_candidates(top_n: int, min_change_pct: float, min_amount_yi: float, pick_count: int):
    live_items, source = try_fetch_live_market(top_n)
    filtered = []
    rejected_largecap = []
    rejected_live = []
    for item in live_items:
        item = {**item, 'style_tags': infer_style(item)}
        if item.get('change_pct', 0) < min_change_pct or item.get('amount_yi', 0) < min_amount_yi:
            rejected_live.append({**item, 'reject_reason': '盘中强度不足'})
            continue
        if not is_smallcap_style(item):
            rejected_largecap.append({**item, 'reject_reason': '大票/权重/非中小盘风格'})
            continue
        filtered.append(item)
    filtered.sort(key=lambda x: (x.get('change_pct', 0), x.get('amount_yi', 0)), reverse=True)
    return filtered[:pick_count], rejected_largecap, rejected_live, source, live_items


def second_round_filter(candidates):
    passed = []
    partial = []
    failed = []
    for item in candidates:
        code = item['code']
        try:
            df = v6.fetch_daily_df(code)
            last = df.tail(4).copy()
            if len(last) < 4:
                raise RuntimeError('not enough rows')
            v3ago = float(last.iloc[0]['volume'])
            vnow = float(last.iloc[3]['volume'])
            c3ago = float(last.iloc[0]['close'])
            cnow = float(last.iloc[3]['close'])
            ma5 = float(last.iloc[3]['ma5']) if pd.notna(last.iloc[3]['ma5']) else None
            volume_up = vnow > v3ago
            price_up = cnow > c3ago
            ma5_ok = (ma5 is not None and cnow >= ma5 * 0.98)
            score = sum([volume_up, price_up, ma5_ok])
            row = {
                **item,
                'volume_3d_up': volume_up,
                'price_3d_up': price_up,
                'ma5_soft_ok': ma5_ok,
                'score': score,
            }
            if score == 3:
                passed.append(row)
            elif score == 2:
                partial.append(row)
            else:
                failed.append(row)
        except Exception as e:
            failed.append({**item, 'error': str(e), 'score': -1})
    passed.sort(key=lambda x: (x.get('change_pct', 0), x.get('amount_yi', 0)), reverse=True)
    partial.sort(key=lambda x: (x.get('change_pct', 0), x.get('amount_yi', 0)), reverse=True)
    failed.sort(key=lambda x: (x.get('change_pct', -999), x.get('amount_yi', 0)), reverse=True)
    return passed, partial, failed


def split_resonance(passed):
    core = []
    follow = []
    for item in passed:
        code = item.get('code', '')
        if code.startswith(('301', '300', '688')) and item.get('change_pct', 0) >= 3:
            core.append(item)
        else:
            follow.append(item)
    return core, follow


def main():
    parser = argparse.ArgumentParser(description=PLUGIN_NAME)
    parser.add_argument('--date', default='today', help='交易日')
    parser.add_argument('--top-n', type=int, default=80, help='实时市场初始抓取范围')
    parser.add_argument('--pick-count', type=int, default=24, help='中小盘候选池上限')
    parser.add_argument('--min-change-pct', type=float, default=1.5, help='最小涨幅过滤')
    parser.add_argument('--min-amount-yi', type=float, default=2.0, help='最小成交额(亿)过滤')
    parser.add_argument('--json', action='store_true', help='输出 JSON')
    args = parser.parse_args()

    candidates, rejected_largecap, rejected_live, source, live_items = first_round_candidates(
        top_n=args.top_n,
        min_change_pct=args.min_change_pct,
        min_amount_yi=args.min_amount_yi,
        pick_count=args.pick_count,
    )
    passed, partial, failed = second_round_filter(candidates)
    core, follow = split_resonance(passed)

    payload = {
        'plugin': PLUGIN_NAME,
        'date': args.date,
        'strategy': '实时强势热股 -> 剔除大票/权重 -> 保留中小盘/创业板/次新/弹性票 -> 近3日量价 + 5日线过滤',
        'market_scan_source': source,
        'top_n': args.top_n,
        'pick_count': args.pick_count,
        'min_change_pct': args.min_change_pct,
        'min_amount_yi': args.min_amount_yi,
        'live_market_pool': live_items,
        'live_smallcap_candidates': candidates,
        'passed': passed,
        'partial': partial,
        'failed': failed,
        'rejected_largecap': rejected_largecap,
        'rejected_live': rejected_live,
        'resonance_core': core,
        'resonance_follow': follow,
        'data_sources': {
            'realtime_scan': source,
            'daily_filter': '腾讯历史K线(akshare)',
            'fallback': '新浪/腾讯候选池fallback',
        },
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print(f'{PLUGIN_NAME} 已运行')
    print(f'策略: {payload["strategy"]}')
    print(f'实时来源: {source}')
    print('盘中中小盘候选：')
    for x in candidates:
        print(f"- {x['name']} {x['code']}  {x['change_pct']}%  成交额{x['amount_yi']}亿  标签:{'/'.join(x.get('style_tags', []))}")
    print('\n第二轮通过：')
    for x in passed:
        print(f"- {x['name']} {x['code']}  score={x['score']}")
    print('\n第二轮部分通过：')
    for x in partial:
        print(f"- {x['name']} {x['code']}  score={x['score']}")
    print('\n剔除的大票/权重：')
    for x in rejected_largecap[:20]:
        print(f"- {x['name']} {x['code']}  {x['change_pct']}%  {x['reject_reason']}")


if __name__ == '__main__':
    main()
