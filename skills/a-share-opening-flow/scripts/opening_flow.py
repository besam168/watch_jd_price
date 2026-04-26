#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import pandas as pd

PLUGIN_NAME = 'A股开盘风向与实时盯盘插件 V6（正式版）'
WORKSPACE = Path(__file__).resolve().parents[3]
HOT_SCRIPT = WORKSPACE / 'skills' / 'a-share-hot-spots' / 'scripts'
SHARED_POOL_DIR = WORKSPACE / 'skills' / 'shared_a_share_pool'
NAME_MAP_CSV = WORKSPACE / 'skills' / 'a-share-hot-spots' / 'references' / 'name_map.csv'
SMALLCAP_UNIVERSE_PATH = WORKSPACE / 'skills' / 'auction_915_925_smooth_scanner' / 'outputs' / 'liutong8yi_marketcap150yi_universe_full.json'
DEFAULT_MAX_FLOAT_MKT_CAP = 150 * 1e8
DEFAULT_MAX_LIUTONGGUBEN = 8 * 1e8
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
SECTOR_NAME_MAP = {
    '��Դ����': '资源周期',
    '����/AI': '算力/AI',
    '���ڿƼ�': '金融科技',
    '����Դ': '新能源',
    '����ҽҩ': '消费医药',
    '��Ѷ/���˰��fallback': '腾讯/新浪候选池fallback',
    'pytdx/通达信协议': 'pytdx/通达信协议',
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
        min_listed_days=120,
        max_float_mkt_cap=DEFAULT_MAX_FLOAT_MKT_CAP,
        max_liutongguben=DEFAULT_MAX_LIUTONGGUBEN,
        limit=limit,
    )
    universe = load_shared_universe(universe_path=SMALLCAP_UNIVERSE_PATH, filters=filters)
    return universe, names_from_universe(universe)


def first_round_candidates():
    sectors = []
    hot = []
    try:
        hot = mw.fetch_hot_stocks()
    except Exception:
        hot = []
    try:
        sectors = mw.fetch_hot_sectors()
    except Exception:
        sectors = []

    shared_universe, shared_name_map = load_shared_pool(limit=3000)
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
        if len(picked) >= 15:
            break

    if not picked:
        fallback_candidates = []
        for item in shared_universe.get('selected', [])[:60]:
            code = str(item.get('code') or '').strip()
            if not code:
                continue
            try:
                stock = mw.fetch_stock(code)
            except Exception:
                continue
            if stock.get('error'):
                continue
            fallback_candidates.append({
                'name': shared_name_map.get(code, CODE_NAME_MAP.get(code, stock.get('name', code))),
                'code': code,
                'change_pct': stock.get('change_pct', 0),
                'amount_yi': stock.get('amount_yi', 0),
            })
        fallback_candidates.sort(key=lambda x: (x.get('change_pct', 0), x.get('amount_yi', 0)), reverse=True)
        picked = fallback_candidates[:15]

    clean_sectors = []
    for sec in sectors[:5]:
        clean_sectors.append({
            'name': SECTOR_NAME_MAP.get(sec.get('name', ''), sec.get('name', '')),
            'change_pct': sec.get('change_pct', 0),
            'leading_stock': CODE_NAME_MAP.get(str(mw.load_name_map().get(sec.get('leading_stock', ''), ''))[-6:], sec.get('leading_stock', '')) if sec.get('leading_stock') else sec.get('leading_stock', ''),
            'leading_change_pct': sec.get('leading_change_pct', 0),
            'amount_yi': sec.get('amount_yi', 0),
            'source': SECTOR_NAME_MAP.get(sec.get('source', ''), sec.get('source', '')),
        })
    return picked, clean_sectors, shared_universe



def second_round_filter(candidates):
    passed = []
    partial = []
    failed = []
    for item in candidates:
        try:
            df = fetch_daily_df(item['code'])
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
    for idx, item in enumerate(sorted(passed, key=lambda x: (x.get('change_pct', 0), x.get('amount_yi', 0), x.get('score', 0)), reverse=True)):
        if idx < 5:
            core.append(item)
        else:
            follow.append(item)
    return core, follow


def sanitize_payload(payload: dict) -> dict:
    sector_name_map = {
        '��Դ����': '资源周期',
        '����/AI': '算力/AI',
        '���ڿƼ�': '金融科技',
        '����Դ': '新能源',
        '����ҽҩ': '消费医药',
    }
    source_map = {
        '��Ѷ/���˰��fallback': '腾讯/新浪候选池fallback',
        'pytdx/通达信协议': 'pytdx/通达信协议',
    }
    leading_stock_map = {
        '�Ͻ��ҵ': '紫金矿业',
        '��о����': '中芯国际',
        '�й�ƽ��': '中国平安',
        '����ʱ��': '宁德时代',
        '����ę́': '贵州茅台',
    }

    def fix_name(code: str, fallback: str) -> str:
        code = str(code or '').strip()
        if code and code in CODE_NAME_MAP:
            return CODE_NAME_MAP[code]
        return fallback

    clean = {
        'plugin': 'A股开盘风向与实时盯盘插件 V6（正式版）',
        'auction_window': payload.get('auction_window', '09:20-09:25'),
        'open_window': payload.get('open_window', '09:30-09:35'),
        'date': payload.get('date', 'today'),
        'top_sectors': [],
        'first_round_candidates': [],
        'passed': [],
        'partial': [],
        'failed': [],
        'resonance_core': [],
        'resonance_follow': [],
    }

    for sec in payload.get('top_sectors', []):
        sec = dict(sec)
        clean['top_sectors'].append({
            'name': sector_name_map.get(sec.get('name', ''), sec.get('name', '')),
            'change_pct': sec.get('change_pct', 0),
            'leading_stock': leading_stock_map.get(sec.get('leading_stock', ''), sec.get('leading_stock', '')),
            'leading_change_pct': sec.get('leading_change_pct', 0),
            'amount_yi': sec.get('amount_yi', 0),
            'source': source_map.get(sec.get('source', ''), sec.get('source', '')),
        })

    for key in ['first_round_candidates', 'passed', 'partial', 'failed', 'resonance_core', 'resonance_follow']:
        for item in payload.get(key, []):
            item = dict(item)
            clean[key].append({
                **item,
                'name': fix_name(item.get('code', ''), item.get('name', '')),
            })

    return clean


def main():
    parser = argparse.ArgumentParser(description=PLUGIN_NAME)
    parser.add_argument('--auction-window', default='09:20-09:25', help='竞价窗口')
    parser.add_argument('--open-window', default='09:30-09:35', help='开盘验证窗口')
    parser.add_argument('--date', default='today', help='交易日')
    parser.add_argument('--json', action='store_true', help='输出 JSON')
    args = parser.parse_args()

    candidates, sectors, shared_universe = first_round_candidates()
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
    payload = sanitize_payload(payload)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print(f'{PLUGIN_NAME} 已运行')
    print(f'竞价窗口: {args.auction_window}')
    print(f'开盘窗口: {args.open_window}')
    print(f'交易日: {args.date}')
    print('最强板块 TOP3：')
    for sec in sectors[:3]:
        print(f"- {sec.get('name', '')}")
    print('\n共振核心：')
    for x in core:
        print(f"- {x['name']} {x['code']}  {x['change_pct']}%  成交额{x['amount_yi']}亿")
    print('\n共振跟随：')
    for x in follow:
        print(f"- {x['name']} {x['code']}  {x['change_pct']}%  成交额{x['amount_yi']}亿")
    print('\n盘中强，但日线不足：')
    for x in partial:
        print(f"- {x['name']} {x['code']}  {x['change_pct']}%  成交额{x['amount_yi']}亿")
    print('\n不通过：')
    for x in failed:
        print(f"- {x['name']} {x['code']}  score={x.get('score', 'NA')}")


if __name__ == '__main__':
    main()
