#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PLUGIN_NAME = 'A股开盘风向与实时盯盘插件 V6（测试版）'
WORKSPACE = Path(__file__).resolve().parents[3]
HOT_SCRIPT = WORKSPACE / 'skills' / 'a-share-hot-spots' / 'scripts'
SHARED_POOL_DIR = WORKSPACE / 'skills' / 'shared_a_share_pool'
NAME_MAP_CSV = WORKSPACE / 'skills' / 'a-share-hot-spots' / 'references' / 'name_map.csv'
sys.path.insert(0, str(HOT_SCRIPT))
sys.path.insert(0, str(SHARED_POOL_DIR.parent))
import market_watch as mw  # type: ignore
from shared_a_share_pool import UniverseFilters, load_shared_universe, names_from_universe


def load_code_name_map() -> dict:
    import csv
    mapping = {}
    if NAME_MAP_CSV.exists():
        with NAME_MAP_CSV.open('r', encoding='utf-8') as f:
            for row in csv.reader(f):
                if len(row) >= 2:
                    mapping[row[1].strip()] = row[0].strip()
    return mapping


CODE_NAME_MAP = load_code_name_map()


CANDIDATE_CODE_MAP = {
    '东岳硅材': '300821',
    '翠微股份': '603123',
    '镇海股份': '603637',
    '中工国际': '002051',
    '中体产业': '600158',
    '通光线缆': '300265',
    '铜冠铜箔': '301217',
    '盛科通信-U': '688702',
    '诚志股份': '000990',
    '诺德股份': '600110',
    '凌玮科技': '301373',
    '同宇新材': '301630',
}


def symbol_of(code: str) -> str:
    if code.startswith('688') or code.startswith('6'):
        return 'sh' + code
    return 'sz' + code


def fetch_daily_df(code: str):
    df = mw.fetch_daily_df_tdx(code, bars=30).copy()
    if df is None or df.empty:
        raise RuntimeError('empty dataframe')
    if 'date' not in df.columns:
        raise RuntimeError(f'bad columns: {list(df.columns)}')
    if 'close' not in df.columns:
        raise RuntimeError(f'bad columns: {list(df.columns)}')
    if 'volume' not in df.columns and 'amount' in df.columns:
        df['volume'] = df['amount']
    need = ['date', 'close', 'volume']
    if not all(x in df.columns for x in need):
        raise RuntimeError(f'bad columns: {list(df.columns)}')
    df = df[need].copy()
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    df = df.dropna().sort_values('date').reset_index(drop=True)
    df['ma5'] = df['close'].rolling(5).mean()
    return df


def load_shared_pool(limit: int | None = None):
    filters = UniverseFilters(
        allow_markets=('sz', 'sh'),
        include_prefixes=('00', '001', '002', '003', '600', '601', '603', '605'),
        exclude_prefixes=('300', '301', '688', '689', '8', '4'),
        exclude_st=True,
        exclude_delisting=True,
        min_listed_days=60,
        max_float_mkt_cap=150 * 1e8,
        max_liutongguben=8 * 1e8,
        limit=limit,
    )
    universe = load_shared_universe(
        universe_path=WORKSPACE / 'skills' / 'auction_915_925_smooth_scanner' / 'outputs' / 'liutong8yi_marketcap150yi_universe_full.json',
        filters=filters,
    )
    return universe, names_from_universe(universe)


def first_round_candidates(limit: int = 12):
    sectors = []
    try:
        hot = mw.fetch_hot_stocks()
    except Exception:
        hot = []
    try:
        sectors = mw.fetch_hot_sectors()
    except Exception:
        sectors = []

    shared_universe, shared_name_map = load_shared_pool(limit=2000)
    allowed_codes = set(shared_name_map.keys())

    picked = []
    for item in hot:
        code = str(item.get('symbol', ''))[-6:]
        if not code or code not in allowed_codes:
            continue
        picked.append({
            'name': shared_name_map.get(code, CODE_NAME_MAP.get(code, item.get('name', ''))),
            'code': code,
            'change_pct': item.get('change_pct', 0),
            'amount_yi': item.get('amount_yi', 0),
        })
        if len(picked) >= limit:
            break

    if not picked:
        fallback_names = ['诚志股份']
        for name in fallback_names:
            code = CANDIDATE_CODE_MAP.get(name)
            if not code:
                continue
            if code not in allowed_codes:
                continue
            picked.append({
                'name': shared_name_map.get(code, CODE_NAME_MAP.get(code, name)),
                'code': code,
                'change_pct': 0,
                'amount_yi': 0,
            })

    return picked, sectors[:5], shared_universe


def fmt_qq_short(payload: dict) -> str:
    lines = [
        'V6-test QQ短报',
        f"股票池: {payload.get('shared_stock_pool', {}).get('selected_count', 0)}只（8亿股+150亿基础池）",
        f"首轮候选: {len(payload.get('first_round_candidates', []))}只",
        f"通过: {len(payload.get('passed', []))}｜部分通过: {len(payload.get('partial', []))}｜不通过: {len(payload.get('failed', []))}",
        '',
        '通过名单：',
    ]
    passed = payload.get('passed', [])
    if passed:
        for x in passed:
            lines.append(f"- {x['name']} {x['code']}｜{x['change_pct']}%｜{x['amount_yi']}亿｜score {x['score']}")
    else:
        lines.append('- 无')
    lines.append('')
    lines.append('部分通过：')
    partial = payload.get('partial', [])
    if partial:
        for x in partial[:10]:
            lines.append(f"- {x['name']} {x['code']}｜{x['change_pct']}%｜{x['amount_yi']}亿｜score {x['score']}")
    else:
        lines.append('- 无')
    lines.append('')
    lines.append('共振跟随：')
    follow = payload.get('resonance_follow', [])
    if follow:
        for x in follow:
            lines.append(f"- {x['name']} {x['code']}")
    else:
        lines.append('- 无')
    return '\n'.join(lines)


def second_round_filter(candidates):
    passed = []
    partial = []
    failed = []
    for item in candidates:
        code = item['code']
        name = item['name']
        try:
            df = fetch_daily_df(code)
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
    return passed, partial, failed


def split_resonance(passed):
    core = []
    follow = []
    core_names = {'东岳硅材', '翠微股份', '中工国际', '盛科通信-U'}
    for item in passed:
        if item['name'] in core_names:
            core.append(item)
        else:
            follow.append(item)
    return core, follow


def main():
    parser = argparse.ArgumentParser(description=PLUGIN_NAME)
    parser.add_argument('--auction-window', default='09:20-09:25', help='竞价窗口')
    parser.add_argument('--open-window', default='09:30-09:35', help='开盘验证窗口')
    parser.add_argument('--date', default='today', help='交易日')
    parser.add_argument('--filter-volume-3d', action='store_true', help='启用近3日放量过滤')
    parser.add_argument('--filter-price-3d', action='store_true', help='启用近3日拉升过滤')
    parser.add_argument('--filter-ma5-soft', action='store_true', help='启用5日线宽松辅助过滤')
    parser.add_argument('--json', action='store_true', help='输出 JSON')
    parser.add_argument('--qq-short', action='store_true', help='输出 QQ 短报版')
    parser.add_argument('--candidate-limit', type=int, default=12, help='首轮候选数量')
    args = parser.parse_args()

    candidates, sectors, shared_universe = first_round_candidates(limit=args.candidate_limit)
    passed, partial, failed = second_round_filter(candidates)
    core, follow = split_resonance(passed)

    payload = {
        'plugin': PLUGIN_NAME,
        'auction_window': args.auction_window,
        'open_window': args.open_window,
        'date': args.date,
        'top_sectors': sectors,
        'first_round_candidates': candidates,
        'passed': passed,
        'partial': partial,
        'failed': failed,
        'resonance_core': core,
        'resonance_follow': follow,
        'shared_stock_pool': {
            'source_module': 'skills/shared_a_share_pool',
            'source_path': shared_universe.get('source_path', ''),
            'selected_count': shared_universe.get('selected_count', 0),
            'filters': shared_universe.get('filters', {}),
        },
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if args.qq_short:
        print(fmt_qq_short(payload))
        return

    print(f'{PLUGIN_NAME} 已运行')
    print(f'竞价窗口: {args.auction_window}')
    print(f'开盘窗口: {args.open_window}')
    print(f'交易日: {args.date}')
    print('第一轮候选池：')
    for x in candidates:
        print(f"- {x['name']} {x['code']}  {x['change_pct']}%  成交额{x['amount_yi']}亿")
    print('\n第二轮通过：')
    for x in passed:
        print(f"- {x['name']} {x['code']}  score={x['score']}")
    print('\n第二轮部分通过：')
    for x in partial:
        print(f"- {x['name']} {x['code']}  score={x['score']}")
    print('\n第二轮不通过：')
    for x in failed:
        print(f"- {x['name']} {x['code']}  score={x.get('score', 'NA')}")
    print('\n共振核心：')
    for x in core:
        print(f"- {x['name']} {x['code']}")
    print('\n共振跟随：')
    for x in follow:
        print(f"- {x['name']} {x['code']}")


if __name__ == '__main__':
    main()
