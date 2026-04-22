#!/usr/bin/env python3
import os
os.environ.setdefault('PYTHONUTF8', '1')
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

import argparse
import io
import json
import statistics
import sys
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path

import pandas as pd

PLUGIN_NAME = 'A股盘中中小盘强势股插件（pytdx版）'
BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE = Path(__file__).resolve().parents[3]
AUCTION_SKILL_DIR = WORKSPACE / 'skills' / 'auction_915_925_smooth_scanner'
AUCTION_DS_DIR = AUCTION_SKILL_DIR / 'datasource'
V6_TEST_SCRIPT = WORKSPACE / 'skills' / 'a-share-opening-flow-v6-test' / 'scripts'

sys.path.insert(0, str(AUCTION_DS_DIR))
sys.path.insert(0, str(V6_TEST_SCRIPT))

from pytdx_snapshot import fetch_quotes_with_fallback  # type: ignore
import opening_flow_v6_test as v6  # type: ignore

UNIVERSE_PATH = AUCTION_SKILL_DIR / 'outputs' / 'liutong5yi_marketcap100yi_universe_full.json'
OUTPUT_DIR = BASE_DIR / 'output'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HIGH_BETA_PREFIX = ('300', '301')
SMALLCAP_ACCEPT_PREFIX = ('000', '001', '002', '003', '600', '601', '603', '605')
EXCLUDED_PREFIX = ('688', '689', '4', '8')


def safe_float(value, default=0.0):
    try:
        if value is None or value == '':
            return default
        return float(value)
    except Exception:
        return default


def normalize_name(text: str) -> str:
    s = str(text or '').strip()
    return s or ''


def market_prefix(code: str) -> str:
    return 'sh' if code.startswith(('60', '68')) else 'sz'


def load_universe() -> list[dict]:
    if not UNIVERSE_PATH.exists():
        raise FileNotFoundError(f'universe_not_found: {UNIVERSE_PATH}')
    obj = json.loads(UNIVERSE_PATH.read_text(encoding='utf-8'))
    selected = obj.get('selected') or []
    out = []
    for item in selected:
        code = str(item.get('code') or '').strip()
        if not code:
            continue
        out.append({
            'code': code,
            'name': normalize_name(item.get('name')),
            'market': item.get('market'),
            'latest_price': safe_float(item.get('latest_price')),
            'liutongguben': safe_float(item.get('liutongguben')),
            'estimated_liutong_marketcap': safe_float(item.get('estimated_liutong_marketcap')),
            'ipo_date': item.get('ipo_date'),
        })
    return out


def chunked(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def collect_snapshot_rows(symbols: list[str], chunk_size: int = 120) -> tuple[list[dict], list[dict]]:
    rows = []
    stats = []
    for chunk in chunked(symbols, chunk_size):
        result = fetch_quotes_with_fallback(chunk, primary_batch_size=5)
        rows.extend(result['rows'])
        stats.append(result['stats'])
    return rows, stats


def reference_price(row: dict) -> float:
    bid1 = safe_float(row.get('bid1'))
    ask1 = safe_float(row.get('ask1'))
    price = safe_float(row.get('price'))
    if bid1 > 0 and ask1 > 0:
        return round((bid1 + ask1) / 2, 4)
    if price > 0:
        return round(price, 4)
    if bid1 > 0:
        return round(bid1, 4)
    if ask1 > 0:
        return round(ask1, 4)
    return 0.0


def build_live_item(row: dict, universe_meta: dict) -> dict:
    code = str(row.get('code') or '').strip()
    current = reference_price(row)
    last_close = safe_float(row.get('last_close'))
    if current <= 0:
        current = last_close
    change = current - last_close if current > 0 and last_close > 0 else 0.0
    change_pct = (change / last_close * 100.0) if last_close > 0 else 0.0
    bid_vol1 = safe_float(row.get('bid_vol1'))
    ask_vol1 = safe_float(row.get('ask_vol1'))
    volume_lot = int(max(bid_vol1, 0) + max(ask_vol1, 0))
    amount_yi = round(current * volume_lot * 100 / 1e8, 2) if current > 0 and volume_lot > 0 else 0.0
    circ_mv_yi = round(safe_float(universe_meta.get('estimated_liutong_marketcap')) / 1e8, 2)
    total_mv_yi = circ_mv_yi
    turnover_ratio = round((amount_yi / circ_mv_yi) * 100.0, 2) if amount_yi > 0 and circ_mv_yi > 0 else 0.0
    return {
        'symbol': f"{market_prefix(code)}{code}",
        'code': code,
        'name': normalize_name(universe_meta.get('name') or row.get('name') or code),
        'current': round(current, 2),
        'change_pct': round(change_pct, 2),
        'change': round(change, 2),
        'volume_lot': volume_lot,
        'amount_yi': amount_yi,
        'total_mv_yi': total_mv_yi,
        'circ_mv_yi': circ_mv_yi,
        'turnover_ratio': turnover_ratio,
        'source': 'pytdx_snapshot_universe',
        'last_close': round(last_close, 2) if last_close > 0 else 0.0,
        'bid1': safe_float(row.get('bid1')),
        'ask1': safe_float(row.get('ask1')),
        'bid_vol1': bid_vol1,
        'ask_vol1': ask_vol1,
        'servertime': row.get('servertime'),
        'liutongguben': universe_meta.get('liutongguben'),
        'estimated_liutong_marketcap': universe_meta.get('estimated_liutong_marketcap'),
        'ipo_date': universe_meta.get('ipo_date'),
    }


def infer_style(item: dict) -> list[str]:
    code = item.get('code', '')
    tags = []
    if code.startswith('301'):
        tags += ['创业板', '次新']
    elif code.startswith('300'):
        tags += ['创业板', '弹性票']
    elif code.startswith(('002', '003')):
        tags += ['中小盘主板']
    elif code.startswith(('603', '605')):
        tags += ['主板弹性票']
    elif code.startswith(('000', '001', '600', '601')):
        tags += ['主板']
    return tags


def classify_cap_bucket(item: dict) -> str:
    ref = max(safe_float(item.get('total_mv_yi')), safe_float(item.get('circ_mv_yi')))
    if ref <= 0:
        return 'unknown'
    if ref <= 100:
        return 'micro'
    if ref <= 300:
        return 'small'
    if ref <= 800:
        return 'mid'
    return 'upper_smallcap'


def is_st_stock(item: dict) -> bool:
    name = str(item.get('name', '') or '').upper().replace(' ', '')
    return 'ST' in name or '*ST' in name or '＊ST' in name or '退' in name


def is_smallcap_style(item: dict, max_total_mv_yi: float, max_circ_mv_yi: float, allow_mainboard_60: bool) -> tuple[bool, str]:
    code = item.get('code', '')
    total_mv = safe_float(item.get('total_mv_yi', 0))
    circ_mv = safe_float(item.get('circ_mv_yi', 0))

    if is_st_stock(item):
        return False, '排除ST/*ST股票'
    if code.startswith(EXCLUDED_PREFIX):
        return False, '排除科创板/北交所'
    if not code.startswith(SMALLCAP_ACCEPT_PREFIX + HIGH_BETA_PREFIX):
        return False, '非目标股票池代码段'
    if total_mv > 0 and total_mv > max_total_mv_yi:
        return False, f'总市值过大>{max_total_mv_yi}亿'
    if circ_mv > 0 and circ_mv > max_circ_mv_yi:
        return False, f'流通市值过大>{max_circ_mv_yi}亿'
    if code.startswith(HIGH_BETA_PREFIX):
        return True, '高弹性代码段'
    if code.startswith(('002', '003', '603', '605', '000', '001')):
        return True, '中小盘主板代码段'
    if code.startswith('60'):
        if allow_mainboard_60:
            return True, '60主板允许纳入'
        return True, '60主板默认纳入新池'
    return True, '5亿股+100亿流通市值新池'


def first_round_candidates(top_n: int, min_change_pct: float, min_amount_yi: float, pick_count: int, max_total_mv_yi: float, max_circ_mv_yi: float, allow_mainboard_60: bool, min_turnover_ratio: float, max_change_pct: float = 999.0):
    universe = load_universe()
    universe_map = {x['code']: x for x in universe}
    codes = list(universe_map.keys())
    rows, fetch_stats = collect_snapshot_rows(codes)

    live_items = []
    for row in rows:
        code = str(row.get('code') or '').strip()
        meta = universe_map.get(code)
        if not meta:
            continue
        item = build_live_item(row, meta)
        live_items.append(item)

    live_items.sort(key=lambda x: (x.get('change_pct', 0), x.get('amount_yi', 0), x.get('turnover_ratio', 0)), reverse=True)
    live_items = live_items[:top_n] if top_n > 0 else live_items

    filtered = []
    rejected_largecap = []
    rejected_live = []
    for item in live_items:
        ok_style, style_reason = is_smallcap_style(item, max_total_mv_yi, max_circ_mv_yi, allow_mainboard_60)
        item = {
            **item,
            'style_tags': infer_style(item),
            'cap_bucket': classify_cap_bucket(item),
        }
        if item.get('change_pct', 0) < min_change_pct or item.get('amount_yi', 0) < min_amount_yi:
            rejected_live.append({**item, 'reject_reason': '盘中强度不足'})
            continue
        if item.get('change_pct', 0) > max_change_pct:
            rejected_live.append({**item, 'reject_reason': f'盘中涨幅过高>{max_change_pct}%'})
            continue
        if safe_float(item.get('turnover_ratio', 0)) > 0 and safe_float(item.get('turnover_ratio', 0)) < min_turnover_ratio:
            rejected_live.append({**item, 'reject_reason': f'换手不足<{min_turnover_ratio}%'})
            continue
        if not ok_style:
            rejected_largecap.append({**item, 'reject_reason': style_reason})
            continue
        filtered.append({**item, 'style_reason': style_reason})
    filtered.sort(key=lambda x: (x.get('change_pct', 0), x.get('amount_yi', 0), x.get('turnover_ratio', 0)), reverse=True)
    return filtered[:pick_count], rejected_largecap, rejected_live, 'pytdx-live-universe', live_items, fetch_stats


def second_round_filter(candidates):
    passed = []
    partial = []
    failed = []
    for item in candidates:
        code = item['code']
        try:
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
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


def estimate_turnover_ratio(item: dict) -> float:
    turnover = safe_float(item.get('turnover_ratio', 0))
    if turnover > 0:
        return round(turnover, 2)
    amount_yi = safe_float(item.get('amount_yi', 0))
    circ_mv_yi = safe_float(item.get('circ_mv_yi', 0))
    if circ_mv_yi > 0 and amount_yi > 0:
        return round((amount_yi / circ_mv_yi) * 100.0, 2)
    return 0.0


def compute_intraday_score(item: dict) -> float:
    change_pct = safe_float(item.get('change_pct', 0))
    amount_yi = safe_float(item.get('amount_yi', 0))
    turnover = estimate_turnover_ratio(item)
    code = item.get('code', '')
    bonus = 0.0
    if code.startswith(HIGH_BETA_PREFIX):
        bonus += 0.8
    elif code.startswith(('002', '003', '603', '605', '000', '001')):
        bonus += 0.4
    if amount_yi >= 15:
        bonus += 1.0
    elif amount_yi >= 8:
        bonus += 0.7
    elif amount_yi >= 4:
        bonus += 0.4
    if turnover >= 25:
        bonus += 1.2
    elif turnover >= 12:
        bonus += 0.7
    elif turnover >= 5:
        bonus += 0.3
    return round(change_pct * 1.2 + bonus, 2)


def compute_conviction(item: dict) -> str:
    change_pct = safe_float(item.get('change_pct', 0))
    amount_yi = safe_float(item.get('amount_yi', 0))
    turnover = estimate_turnover_ratio(item)
    if change_pct >= 8 and amount_yi >= 8 and turnover >= 5:
        return '高'
    if change_pct >= 4 and amount_yi >= 3:
        return '中'
    return '一般'


def attach_intraday_metrics(items: list) -> list:
    out = []
    for item in items:
        est_turnover = estimate_turnover_ratio(item)
        out.append({
            **item,
            'turnover_ratio_est': est_turnover,
            'turnover_ratio_effective': est_turnover,
            'intraday_score': compute_intraday_score(item),
            'conviction': compute_conviction(item),
        })
    out.sort(key=lambda x: (x.get('intraday_score', 0), x.get('amount_yi', 0)), reverse=True)
    return out


def classify_trading_roles(passed: list, partial: list, failed: list) -> tuple[list, list, list]:
    passed = attach_intraday_metrics(passed)
    partial = attach_intraday_metrics(partial)
    failed = attach_intraday_metrics(failed)

    true_leaders = []
    strong_followers = []
    for idx, item in enumerate(passed):
        code = item.get('code', '')
        change_pct = item.get('change_pct', 0)
        amount_yi = item.get('amount_yi', 0)
        high_beta = code.startswith(HIGH_BETA_PREFIX)
        if (high_beta and change_pct >= 2.0 and amount_yi >= 4.0) or change_pct >= 5.0 or (idx < 2 and item.get('intraday_score', 0) >= 3.2):
            true_leaders.append(item)
        else:
            strong_followers.append(item)

    pseudo_pool = partial + [x for x in failed if x.get('change_pct', 0) >= 1.0]
    pseudo_pool.sort(key=lambda x: (x.get('intraday_score', 0), x.get('amount_yi', 0)), reverse=True)
    pseudo_strong = pseudo_pool
    return true_leaders, strong_followers, pseudo_strong


def build_watchlist(true_leaders: list, strong_followers: list) -> list:
    return (true_leaders + strong_followers)[:5]


def format_turnover_display(item: dict) -> str:
    raw = safe_float(item.get('turnover_ratio', 0))
    effective = safe_float(item.get('turnover_ratio_effective', 0))
    estimated = safe_float(item.get('turnover_ratio_est', 0))
    if raw > 0:
        return f'{raw}%'
    if estimated > 0:
        return f'≈{effective}%'
    return '0.0%'


def build_role_board(true_leaders: list, strong_followers: list, pseudo_strong: list) -> dict:
    def brief(item):
        if not item:
            return None
        return {
            'name': item.get('name'),
            'code': item.get('code'),
            'change_pct': item.get('change_pct'),
            'amount_yi': item.get('amount_yi'),
            'turnover': format_turnover_display(item),
            'conviction': item.get('conviction'),
        }
    return {
        'dragon_one': brief(true_leaders[0]) if len(true_leaders) >= 1 else None,
        'dragon_two': brief(true_leaders[1]) if len(true_leaders) >= 2 else None,
        'followers': [brief(x) for x in strong_followers[:3]],
        'observe': [brief(x) for x in pseudo_strong[:5]],
    }


def build_chinese_summary(true_leaders: list, strong_followers: list, pseudo_strong: list, watchlist: list) -> dict:
    def pack(items):
        return [f"{x['name']} {x['code']}" for x in items[:3]]
    leader_names = pack(true_leaders)
    follower_names = pack(strong_followers)
    pseudo_names = pack(pseudo_strong)
    watch_names = pack(watchlist)
    if leader_names:
        overall = f"盘中中小盘强势股里，最强的是 {'、'.join(leader_names)}。"
    elif watch_names:
        overall = f"盘中中小盘候选偏少，当前先看 {'、'.join(watch_names)}。"
    else:
        overall = '这会儿中小盘真正走出来的票不多，先别硬做。'
    return {
        'overall': overall,
        'true_leaders': leader_names,
        'strong_followers': follower_names,
        'pseudo_strong': pseudo_names,
        'watchlist': watch_names,
    }


def main():
    parser = argparse.ArgumentParser(description=PLUGIN_NAME)
    parser.add_argument('--date', default='today', help='交易日')
    parser.add_argument('--top-n', type=int, default=120, help='实时市场初始抓取范围')
    parser.add_argument('--pick-count', type=int, default=24, help='中小盘候选池上限')
    parser.add_argument('--min-change-pct', type=float, default=1.5, help='最小涨幅过滤')
    parser.add_argument('--min-amount-yi', type=float, default=0.03, help='最小成交额(亿)过滤')
    parser.add_argument('--min-turnover-ratio', type=float, default=0.0, help='最小换手率过滤(%)')
    parser.add_argument('--max-total-mv-yi', type=float, default=100.0, help='总市值上限(亿)')
    parser.add_argument('--max-circ-mv-yi', type=float, default=100.0, help='流通市值上限(亿)')
    parser.add_argument('--allow-mainboard-60', action='store_true', help='允许60主板在满足阈值时入选')
    parser.add_argument('--max-change-pct', type=float, default=999.0, help='盘中最大涨幅过滤')
    parser.add_argument('--under-five-mode', action='store_true', help='盘中只保留涨幅不超过5%的票')
    parser.add_argument('--output-json', default='', help='把结果额外写入指定 JSON 文件')
    parser.add_argument('--boss-brief', action='store_true', help='输出老板播报版（精简）')
    parser.add_argument('--json', action='store_true', help='输出 JSON')
    args = parser.parse_args()

    effective_max_change_pct = 5.0 if args.under_five_mode else args.max_change_pct

    candidates, rejected_largecap, rejected_live, source, live_items, fetch_stats = first_round_candidates(
        top_n=args.top_n,
        min_change_pct=args.min_change_pct,
        min_amount_yi=args.min_amount_yi,
        pick_count=args.pick_count,
        max_total_mv_yi=args.max_total_mv_yi,
        max_circ_mv_yi=args.max_circ_mv_yi,
        allow_mainboard_60=args.allow_mainboard_60,
        min_turnover_ratio=args.min_turnover_ratio,
        max_change_pct=effective_max_change_pct,
    )
    passed, partial, failed = second_round_filter(candidates)
    true_leaders, strong_followers, pseudo_strong = classify_trading_roles(passed, partial, failed)
    watchlist = build_watchlist(true_leaders, strong_followers)
    role_board = build_role_board(true_leaders, strong_followers, pseudo_strong)
    chinese_summary = build_chinese_summary(true_leaders, strong_followers, pseudo_strong, watchlist)

    payload = {
        'plugin': PLUGIN_NAME,
        'version': 'v5-pytdx',
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'date': args.date,
        'strategy': '停用东财/新浪实时入口，改用pytdx快照+5亿股100亿流通市值新股票池，再叠加近3日量价+5日线过滤',
        'market_scan_source': source,
        'top_n': args.top_n,
        'pick_count': args.pick_count,
        'min_change_pct': args.min_change_pct,
        'min_amount_yi': args.min_amount_yi,
        'min_turnover_ratio': args.min_turnover_ratio,
        'max_change_pct': effective_max_change_pct,
        'under_five_mode': args.under_five_mode,
        'max_total_mv_yi': args.max_total_mv_yi,
        'max_circ_mv_yi': args.max_circ_mv_yi,
        'allow_mainboard_60': args.allow_mainboard_60,
        'live_market_pool': live_items,
        'live_smallcap_candidates': candidates,
        'passed': passed,
        'partial': partial,
        'failed': failed,
        'true_leaders': true_leaders,
        'strong_followers': strong_followers,
        'pseudo_strong': pseudo_strong,
        'watchlist': watchlist,
        'role_board': role_board,
        'chinese_summary': chinese_summary,
        'rejected_largecap': rejected_largecap,
        'rejected_live': rejected_live,
        'fetch_stats': fetch_stats,
        'data_sources': {
            'realtime_scan': source,
            'primary': 'pytdx.hq.TdxHq_API',
            'secondary': 'disabled',
            'daily_filter': '腾讯历史K线(akshare)',
            'fallback': 'pytdx多服务器fallback + 单批失败降级补拉',
            'universe': str(UNIVERSE_PATH),
            'legacy_eastmoney': 'disabled',
            'legacy_sina': 'disabled',
        },
    }

    if args.output_json:
        out_path = Path(args.output_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print(f'{PLUGIN_NAME} 已运行')
    print(f'策略: {payload["strategy"]}')
    print(f'实时来源: {source}')
    print(f"结论: {chinese_summary['overall']}")
    if role_board.get('dragon_one'):
        x = role_board['dragon_one']
        print(f"龙一: {x['name']} {x['code']}  {x['change_pct']}%  成交额{x['amount_yi']}亿  换手{x['turnover']}  信号{x['conviction']}")
    if role_board.get('dragon_two'):
        x = role_board['dragon_two']
        print(f"龙二: {x['name']} {x['code']}  {x['change_pct']}%  成交额{x['amount_yi']}亿  换手{x['turnover']}  信号{x['conviction']}")
    if role_board.get('followers'):
        print('跟随:')
        for x in role_board['followers']:
            print(f"- {x['name']} {x['code']}  {x['change_pct']}%  成交额{x['amount_yi']}亿  换手{x['turnover']}  信号{x['conviction']}")
    if role_board.get('observe'):
        print('观察:')
        for x in role_board['observe']:
            print(f"- {x['name']} {x['code']}  {x['change_pct']}%  成交额{x['amount_yi']}亿  换手{x['turnover']}  信号{x['conviction']}")

    if args.boss_brief:
        return

    print('真龙头：')
    for x in true_leaders:
        print(f"- {x['name']} {x['code']}  {x['change_pct']}%  成交额{x['amount_yi']}亿  换手{format_turnover_display(x)}")
    print('\n强跟风：')
    for x in strong_followers:
        print(f"- {x['name']} {x['code']}  {x['change_pct']}%  成交额{x['amount_yi']}亿  换手{format_turnover_display(x)}")
    print('\n伪强票：')
    for x in pseudo_strong[:10]:
        print(f"- {x['name']} {x['code']}  {x.get('change_pct', 0)}%  score={x.get('score', 'NA')}")


if __name__ == '__main__':
    main()
