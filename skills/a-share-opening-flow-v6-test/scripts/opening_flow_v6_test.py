#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

import akshare as ak
import pandas as pd

PLUGIN_NAME = 'A股开盘风向与实时盯盘插件 V6（测试版）'
WORKSPACE = Path(__file__).resolve().parents[3]
HOT_SCRIPT = WORKSPACE / 'skills' / 'a-share-hot-spots' / 'scripts'
sys.path.insert(0, str(HOT_SCRIPT))
import market_watch as mw  # type: ignore


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
    symbol = symbol_of(code)
    df = ak.stock_zh_a_hist_tx(symbol=symbol, start_date='20260101', end_date='20500101', adjust='')
    if df is None or df.empty:
        raise RuntimeError('empty dataframe')
    rename_map = {}
    for col in df.columns:
        c = str(col).strip()
        if c in ['date', '日期']:
            rename_map[col] = 'date'
        elif c in ['close', '收盘']:
            rename_map[col] = 'close'
        elif c in ['amount', '成交量', 'volume']:
            rename_map[col] = 'volume'
    df = df.rename(columns=rename_map)
    need = ['date', 'close', 'volume']
    if not all(x in df.columns for x in need):
        raise RuntimeError(f'bad columns: {list(df.columns)}')
    df = df[need].copy()
    df['date'] = pd.to_datetime(df['date'])
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    df = df.dropna().sort_values('date').reset_index(drop=True)
    df['ma5'] = df['close'].rolling(5).mean()
    return df


def first_round_candidates():
    sectors = []
    try:
        hot = mw.fetch_hot_stocks()
    except Exception:
        hot = []
    try:
        sectors = mw.fetch_hot_sectors()
    except Exception:
        sectors = []

    picked = []
    for item in hot[:12]:
        code = str(item.get('symbol', ''))[-6:]
        picked.append({
            'name': item.get('name', ''),
            'code': code,
            'change_pct': item.get('change_pct', 0),
            'amount_yi': item.get('amount_yi', 0),
        })

    if not picked:
        fallback_names = ['东岳硅材', '翠微股份', '镇海股份', '中工国际', '中体产业', '通光线缆', '铜冠铜箔', '盛科通信-U', '诚志股份', '诺德股份', '凌玮科技', '同宇新材']
        for name in fallback_names:
            picked.append({
                'name': name,
                'code': CANDIDATE_CODE_MAP[name],
                'change_pct': 0,
                'amount_yi': 0,
            })

    return picked, sectors[:5]


def second_round_filter(candidates):
    passed = []
    partial = []
    failed = []
    for item in candidates:
        code = item['code']
        name = item['name']
        # 新增过滤规则：排除科创板、排除N字头新股、排除创业板
        if code.startswith('688'):
            failed.append({**item, 'error': '科创板股票自动排除', 'score': -1})
            continue
        if code.startswith('300'):
            failed.append({**item, 'error': '创业板股票自动排除', 'score': -1})
            continue
        if name.startswith('N'):
            failed.append({**item, 'error': 'N字头新股自动排除', 'score': -1})
            continue
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
    args = parser.parse_args()

    candidates, sectors = first_round_candidates()
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
        'data_sources': {
            'eastmoney_enabled': False,
            'realtime_candidates': '新浪/腾讯fallback',
            'daily_filter': '腾讯历史K线(akshare)',
            'sector_source': '新浪/腾讯分组fallback',
        },
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
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
