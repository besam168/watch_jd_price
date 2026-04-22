#!/usr/bin/env python3
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import akshare as ak
import pandas as pd

PLUGIN_NAME = 'A股开盘风向与实时盯盘插件 V6（正式版）'
WORKSPACE = Path(__file__).resolve().parents[3]
HOT_SCRIPT = WORKSPACE / 'skills' / 'a-share-hot-spots' / 'scripts'
NAME_MAP_CSV = WORKSPACE / 'skills' / 'a-share-hot-spots' / 'references' / 'name_map.csv'
sys.path.insert(0, str(HOT_SCRIPT))
import market_watch as mw  # type: ignore


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
    hot = []
    try:
        hot = mw.fetch_hot_stocks()
    except Exception:
        hot = []
    try:
        sectors = mw.fetch_hot_sectors()
    except Exception:
        sectors = []

    picked = []
    for item in hot[:15]:
        code = str(item.get('symbol', ''))[-6:]
        if not code:
            continue
        picked.append({
            'name': CODE_NAME_MAP.get(code, item.get('name', '')),
            'code': code,
            'change_pct': item.get('change_pct', 0),
            'amount_yi': item.get('amount_yi', 0),
        })

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
    return picked, clean_sectors


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
        '��Ѷ/���˰��fallback': '新浪/腾讯候选池fallback',
        '新浪/腾讯候选池fallback': '新浪/腾讯候选池fallback',
        '新浪/腾讯板块fallback': '新浪/腾讯板块fallback',
        '东方财富': '东方财富',
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


def build_sector_strength_text(sectors: list[dict]) -> str:
    lines = ['板块强弱结果']
    if not sectors:
        lines.append('今日暂无有效板块结果')
        return '\n'.join(lines)
    for idx, sec in enumerate(sectors[:10], 1):
        sign = '+' if float(sec.get('change_pct', 0) or 0) >= 0 else ''
        lines.append(
            f"{idx}. {sec.get('name', '')} {sign}{sec.get('change_pct', 0)}%｜龙头 {sec.get('leading_stock', '-') or '-'}｜来源 {sec.get('source', '-') or '-'}"
        )
    return '\n'.join(lines)


def build_leaderboard_text(core: list[dict], follow: list[dict], partial: list[dict]) -> str:
    lines = ['龙头股结果', '']
    lines.append('核心龙头：')
    if core:
        for idx, x in enumerate(core, 1):
            sign = '+' if float(x.get('change_pct', 0) or 0) >= 0 else ''
            lines.append(f"{idx}. {x['name']} {x['code']}｜{sign}{x['change_pct']}%｜成交额{x['amount_yi']}亿")
    else:
        lines.append('暂无')
    lines.append('')
    lines.append('跟随龙头：')
    if follow:
        for idx, x in enumerate(follow, 1):
            sign = '+' if float(x.get('change_pct', 0) or 0) >= 0 else ''
            lines.append(f"{idx}. {x['name']} {x['code']}｜{sign}{x['change_pct']}%｜成交额{x['amount_yi']}亿")
    else:
        lines.append('暂无')
    lines.append('')
    lines.append('次级关注：')
    if partial:
        for idx, x in enumerate(partial[:10], 1):
            sign = '+' if float(x.get('change_pct', 0) or 0) >= 0 else ''
            lines.append(f"{idx}. {x['name']} {x['code']}｜{sign}{x['change_pct']}%｜成交额{x['amount_yi']}亿")
    else:
        lines.append('暂无')
    return '\n'.join(lines)


def build_brief_text(payload: dict, sectors: list[dict], core: list[dict], follow: list[dict], partial: list[dict]) -> str:
    lines = [
        f"{PLUGIN_NAME} 简报",
        f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"竞价窗口：{payload.get('auction_window', '')}",
        f"开盘窗口：{payload.get('open_window', '')}",
        '',
        '最强板块：',
    ]
    if sectors:
        for idx, sec in enumerate(sectors[:3], 1):
            sign = '+' if float(sec.get('change_pct', 0) or 0) >= 0 else ''
            lines.append(f"{idx}. {sec.get('name', '')} {sign}{sec.get('change_pct', 0)}%")
    else:
        lines.append('暂无')
    lines.append('')
    lines.append('核心龙头：')
    if core:
        for idx, x in enumerate(core[:5], 1):
            sign = '+' if float(x.get('change_pct', 0) or 0) >= 0 else ''
            lines.append(f"{idx}. {x['name']} {x['code']} {sign}{x['change_pct']}%")
    else:
        lines.append('暂无')
    lines.append('')
    lines.append('跟随龙头：')
    if follow:
        for idx, x in enumerate(follow[:5], 1):
            sign = '+' if float(x.get('change_pct', 0) or 0) >= 0 else ''
            lines.append(f"{idx}. {x['name']} {x['code']} {sign}{x['change_pct']}%")
    else:
        lines.append('暂无')
    lines.append('')
    lines.append('次级关注：')
    if partial:
        for idx, x in enumerate(partial[:5], 1):
            sign = '+' if float(x.get('change_pct', 0) or 0) >= 0 else ''
            lines.append(f"{idx}. {x['name']} {x['code']} {sign}{x['change_pct']}%")
    else:
        lines.append('暂无')
    return '\n'.join(lines)


def write_output_files(payload: dict, sectors: list[dict], core: list[dict], follow: list[dict], partial: list[dict]) -> dict:
    out_dir = WORKSPACE / 'skills' / 'a-share-opening-flow' / 'output'
    out_dir.mkdir(parents=True, exist_ok=True)
    brief_path = out_dir / 'latest_brief.txt'
    sector_path = out_dir / 'latest_sector_strength.txt'
    leader_path = out_dir / 'latest_leaders.txt'
    json_path = out_dir / 'latest_output.json'

    brief_text = build_brief_text(payload, sectors, core, follow, partial)
    sector_text = build_sector_strength_text(sectors)
    leader_text = build_leaderboard_text(core, follow, partial)

    brief_path.write_text(brief_text, encoding='utf-8')
    sector_path.write_text(sector_text, encoding='utf-8')
    leader_path.write_text(leader_text, encoding='utf-8')
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    return {
        'brief': str(brief_path),
        'sector_strength': str(sector_path),
        'leaders': str(leader_path),
        'json': str(json_path),
    }


def main():
    parser = argparse.ArgumentParser(description=PLUGIN_NAME)
    parser.add_argument('--auction-window', default='09:20-09:25', help='竞价窗口')
    parser.add_argument('--open-window', default='09:30-09:35', help='开盘验证窗口')
    parser.add_argument('--date', default='today', help='交易日')
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
            'eastmoney_enabled': True,
            'realtime_candidates': '东方财富→新浪→腾讯',
            'daily_filter': '腾讯历史K线(akshare)',
            'sector_source': '东方财富→新浪/腾讯分组fallback',
        },
    }
    payload = sanitize_payload(payload)
    output_files = write_output_files(payload, sectors, core, follow, partial)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print(f'{PLUGIN_NAME} 已运行')
    print(f'竞价窗口: {args.auction_window}')
    print(f'开盘窗口: {args.open_window}')
    print(f'交易日: {args.date}')
    print(f"简报文件: {output_files['brief']}")
    print(f"板块强弱结果: {output_files['sector_strength']}")
    print(f"龙头股结果: {output_files['leaders']}")
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
