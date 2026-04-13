#!/usr/bin/env python3
import os
os.environ.setdefault('PYTHONUTF8', '1')
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

import pandas as pd

try:
    import io
    from contextlib import redirect_stderr, redirect_stdout
except Exception:
    io = None
    redirect_stderr = None
    redirect_stdout = None

PLUGIN_NAME = 'A股盘中中小盘强势股插件（实时版）'
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
    '600519', '300750', '000858', '600036', '600030', '300059', '002594', '601318', '601012', '601138',
    '688981', '688256', '601899', '601888', '000651', '000333', '603259', '002475', '688041', '300308',
    '000977', '002230', '603019', '600900', '601127', '601919', '601336', '600031', '002241', '002714',
    '600438', '603501', '002371', '603986', '002463', '600019', '601857', '601088', '000001', '000002'
}
HIGH_BETA_PREFIX = ('300', '301', '688')
SMALLCAP_ACCEPT_PREFIX = ('300', '301', '688', '002', '003', '603', '605')
SINA_ALL_MARKET_URL = 'https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page={page}&num={num}&sort=changepercent&asc=0&node=hs_a&symbol=&_s_r_a=page'


def normalize_name(text: str) -> str:
    if not text:
        return text
    try:
        fixed = mw._decode_possible_garbled(text)
        return fixed or text
    except Exception:
        return text


def fetch_text_direct(url: str, referer: str | None = None, timeout: int = 12) -> str:
    headers = dict(mw.HEADERS)
    if referer:
        headers['Referer'] = referer
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    last_error = None
    for _ in range(3):
        try:
            req = urllib.request.Request(url, headers=headers)
            with opener.open(req, timeout=timeout) as resp:
                raw = resp.read()
                charset = 'gbk' if 'sina' in url or 'sinajs' in url else 'utf-8'
                return raw.decode(charset, errors='replace')
        except Exception as e:
            last_error = e
    raise last_error


def build_live_item(code: str, name: str, current, change_pct, change, volume_lot, amount_yi, total_mv_yi=0.0, circ_mv_yi=0.0, source='', turnover_ratio=0.0) -> dict:
    market = 'sh' if code.startswith(('60', '68')) else 'sz'
    return {
        'symbol': f'{market}{code}',
        'code': code,
        'name': normalize_name(name) or CODE_NAME_MAP.get(code, code),
        'current': round(mw.safe_float(current), 2),
        'change_pct': round(mw.safe_float(change_pct), 2),
        'change': round(mw.safe_float(change), 2),
        'volume_lot': int(mw.safe_float(volume_lot)),
        'amount_yi': round(mw.safe_float(amount_yi), 2),
        'total_mv_yi': round(mw.safe_float(total_mv_yi), 2),
        'circ_mv_yi': round(mw.safe_float(circ_mv_yi), 2),
        'turnover_ratio': round(mw.safe_float(turnover_ratio), 2),
        'source': source,
    }


def try_fetch_live_market_from_sina(top_n: int) -> tuple[list, str]:
    per_page = 80
    pages = max(1, (top_n + per_page - 1) // per_page)
    out = []
    for page in range(1, pages + 1):
        url = SINA_ALL_MARKET_URL.format(page=page, num=per_page)
        raw = fetch_text_direct(url, referer='https://finance.sina.com.cn')
        items = json.loads(raw)
        for item in items:
            code = str(item.get('code', '')).strip()
            if not re.fullmatch(r'\d{6}', code):
                continue
            out.append(build_live_item(
                code=code,
                name=str(item.get('name', '')).strip(),
                current=item.get('trade', 0),
                change_pct=item.get('changepercent', 0),
                change=item.get('pricechange', 0),
                volume_lot=item.get('volume', 0),
                amount_yi=mw.safe_float(item.get('amount', 0)) / 1e8,
                total_mv_yi=mw.safe_float(item.get('mktcap', 0)) / 1e4,
                circ_mv_yi=mw.safe_float(item.get('nmc', 0)) / 1e4,
                turnover_ratio=item.get('turnoverratio', 0),
                source='新浪全市场涨幅榜',
            ))
    out.sort(key=lambda x: (x.get('change_pct', 0), x.get('amount_yi', 0)), reverse=True)
    return out[:top_n], 'sina-all-market'


def try_fetch_live_market_from_eastmoney(top_n: int) -> tuple[list, str]:
    urls = [
        (
            f'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz={top_n}&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281'
            '&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14,f2,f3,f4,f5,f6,f20,f21'
        ),
        (
            f'http://push2.eastmoney.com/api/qt/clist/get?pn=1&pz={top_n}&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281'
            '&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14,f2,f3,f4,f5,f6,f20,f21'
        ),
    ]
    for url in urls:
        try:
            raw = fetch_text_direct(url, referer='https://quote.eastmoney.com')
            obj = json.loads(raw)
            diff = ((obj.get('data') or {}).get('diff') or [])
            out = []
            for item in diff:
                code = str(item.get('f12', '')).strip()
                if not re.fullmatch(r'\d{6}', code):
                    continue
                out.append(build_live_item(
                    code=code,
                    name=str(item.get('f14', '')).strip(),
                    current=item.get('f2', 0),
                    change_pct=item.get('f3', 0),
                    change=item.get('f4', 0),
                    volume_lot=item.get('f5', 0),
                    amount_yi=mw.safe_float(item.get('f6', 0)) / 1e8,
                    total_mv_yi=mw.safe_float(item.get('f20', 0)) / 1e8,
                    circ_mv_yi=mw.safe_float(item.get('f21', 0)) / 1e8,
                    source='东方财富实时全市场',
                ))
            if out:
                out.sort(key=lambda x: (x.get('change_pct', 0), x.get('amount_yi', 0)), reverse=True)
                return out, 'eastmoney-live'
        except Exception:
            continue
    return [], 'eastmoney-failed'


def fetch_builtin_smallcap_live_pool() -> list:
    out = []
    for name, code in v6.CANDIDATE_CODE_MAP.items():
        try:
            stock = mw.fetch_stock(code)
        except Exception:
            continue
        if stock.get('error'):
            continue
        out.append(build_live_item(
            code=code,
            name=name,
            current=stock.get('current', 0),
            change_pct=stock.get('change_pct', 0),
            change=stock.get('change', 0),
            volume_lot=stock.get('volume_lot', 0),
            amount_yi=stock.get('amount_yi', 0),
            source='V6内置中小盘池',
        ))
    out.sort(key=lambda x: (x.get('change_pct', 0), x.get('amount_yi', 0)), reverse=True)
    return out


def merge_unique_by_code(*groups: list) -> list:
    merged = []
    seen = set()
    for group in groups:
        for item in group:
            code = str(item.get('code', '')).strip()
            if not code or code in seen:
                continue
            seen.add(code)
            merged.append(item)
    return merged


def try_fetch_live_market(top_n: int) -> tuple[list, str]:
    eastmoney_items, eastmoney_source = try_fetch_live_market_from_eastmoney(top_n)
    if eastmoney_items:
        return eastmoney_items[:top_n], eastmoney_source

    try:
        sina_items, sina_source = try_fetch_live_market_from_sina(top_n)
        if sina_items:
            return sina_items, sina_source
    except Exception:
        pass

    hot_items = []
    try:
        for item in mw.fetch_hot_stocks():
            code = str(item.get('symbol', ''))[-6:]
            hot_items.append(build_live_item(
                code=code,
                name=str(item.get('name', '')).strip(),
                current=item.get('current', 0),
                change_pct=item.get('change_pct', 0),
                change=item.get('change', 0),
                volume_lot=item.get('volume_lot', 0),
                amount_yi=item.get('amount_yi', 0),
                source=item.get('source', '新浪/腾讯候选池fallback'),
            ))
    except Exception:
        hot_items = []

    builtin_smallcap = fetch_builtin_smallcap_live_pool()
    merged = merge_unique_by_code(hot_items, builtin_smallcap)
    merged.sort(key=lambda x: (x.get('change_pct', 0), x.get('amount_yi', 0)), reverse=True)
    return merged[: max(top_n, 24)], 'fallback-hot-stocks+builtin-smallcap'


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
    elif code.startswith(('603', '605')):
        tags += ['主板弹性票']
    elif code.startswith('60'):
        tags += ['主板']
    return tags


def classify_cap_bucket(item: dict) -> str:
    total_mv = mw.safe_float(item.get('total_mv_yi', 0))
    circ_mv = mw.safe_float(item.get('circ_mv_yi', 0))
    if total_mv <= 0 and circ_mv <= 0:
        return 'unknown'
    ref = max(total_mv, circ_mv)
    if ref <= 300:
        return 'small'
    if ref <= 1000:
        return 'mid'
    if ref <= 3000:
        return 'large'
    return 'mega'


def is_smallcap_style(item: dict, max_total_mv_yi: float, max_circ_mv_yi: float, allow_mainboard_60: bool) -> tuple[bool, str]:
    code = item.get('code', '')
    total_mv = mw.safe_float(item.get('total_mv_yi', 0))
    circ_mv = mw.safe_float(item.get('circ_mv_yi', 0))

    if code in LARGE_CAP_CODES:
        return False, '命中大票/权重黑名单'
    if total_mv > 0 and total_mv > max_total_mv_yi:
        return False, f'总市值过大>{max_total_mv_yi}亿'
    if circ_mv > 0 and circ_mv > max_circ_mv_yi:
        return False, f'流通市值过大>{max_circ_mv_yi}亿'
    if code.startswith(HIGH_BETA_PREFIX):
        return True, '高弹性代码段'
    if code.startswith(('002', '003', '603', '605')):
        return True, '中小盘/弹性主板代码段'
    if code.startswith('60'):
        if not allow_mainboard_60:
            return False, '默认排除60主板大票风格'
        if total_mv > 0 and total_mv <= max_total_mv_yi and circ_mv <= max_circ_mv_yi:
            return True, '60主板但市值未超阈值'
        return False, '60主板且不满足小中盘阈值'
    if total_mv > 0 and total_mv <= max_total_mv_yi and circ_mv <= max_circ_mv_yi:
        return True, '市值阈值通过'
    return False, '非中小盘风格'


def first_round_candidates(top_n: int, min_change_pct: float, min_amount_yi: float, pick_count: int, max_total_mv_yi: float, max_circ_mv_yi: float, allow_mainboard_60: bool, min_turnover_ratio: float):
    live_items, source = try_fetch_live_market(top_n)
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
        if mw.safe_float(item.get('turnover_ratio', 0)) > 0 and mw.safe_float(item.get('turnover_ratio', 0)) < min_turnover_ratio:
            rejected_live.append({**item, 'reject_reason': f'换手不足<{min_turnover_ratio}%'})
            continue
        if not ok_style:
            rejected_largecap.append({**item, 'reject_reason': style_reason})
            continue
        filtered.append({**item, 'style_reason': style_reason})
    filtered.sort(key=lambda x: (x.get('change_pct', 0), x.get('amount_yi', 0), x.get('turnover_ratio', 0)), reverse=True)
    return filtered[:pick_count], rejected_largecap, rejected_live, source, live_items


def second_round_filter(candidates):
    passed = []
    partial = []
    failed = []
    for item in candidates:
        code = item['code']
        try:
            if io is not None and redirect_stdout is not None and redirect_stderr is not None:
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    df = v6.fetch_daily_df(code)
            else:
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
    turnover = mw.safe_float(item.get('turnover_ratio', 0))
    if turnover > 0:
        return round(turnover, 2)

    amount_yi = mw.safe_float(item.get('amount_yi', 0))
    circ_mv_yi = mw.safe_float(item.get('circ_mv_yi', 0))
    current = mw.safe_float(item.get('current', 0))
    change = mw.safe_float(item.get('change', 0))
    prev_close = current - change if current > 0 else 0.0

    est = 0.0
    if circ_mv_yi > 0 and amount_yi > 0:
        est = (amount_yi / circ_mv_yi) * 100.0
    elif prev_close > 0 and amount_yi > 0:
        est = (amount_yi / (prev_close * 10.0)) * 0.01

    if est <= 0:
        return 0.0
    return round(est, 2)


def compute_intraday_score(item: dict) -> float:
    change_pct = mw.safe_float(item.get('change_pct', 0))
    amount_yi = mw.safe_float(item.get('amount_yi', 0))
    turnover = estimate_turnover_ratio(item)
    code = item.get('code', '')
    bonus = 0.0
    if code.startswith(HIGH_BETA_PREFIX):
        bonus += 0.8
    elif code.startswith(('002', '003', '603', '605')):
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
    change_pct = mw.safe_float(item.get('change_pct', 0))
    amount_yi = mw.safe_float(item.get('amount_yi', 0))
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


def classify_trading_roles(passed: list, partial: list, failed: list) -> tuple[list, list, list]:
    passed = attach_intraday_metrics(passed)
    partial = attach_intraday_metrics(partial)
    failed = attach_intraday_metrics(failed)

    true_leaders = []
    strong_followers = []
    pseudo_strong = []

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
    merged = true_leaders + strong_followers
    return merged[:5]


def format_turnover_display(item: dict) -> str:
    raw = mw.safe_float(item.get('turnover_ratio', 0))
    effective = mw.safe_float(item.get('turnover_ratio_effective', 0))
    estimated = mw.safe_float(item.get('turnover_ratio_est', 0))
    if raw > 0:
        return f"{raw}%"
    if estimated > 0:
        return f"≈{effective}%"
    return "0.0%"


def main():
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    parser = argparse.ArgumentParser(description=PLUGIN_NAME)
    parser.add_argument('--date', default='today', help='交易日')
    parser.add_argument('--top-n', type=int, default=120, help='实时市场初始抓取范围')
    parser.add_argument('--pick-count', type=int, default=24, help='中小盘候选池上限')
    parser.add_argument('--min-change-pct', type=float, default=1.5, help='最小涨幅过滤')
    parser.add_argument('--min-amount-yi', type=float, default=2.0, help='最小成交额(亿)过滤')
    parser.add_argument('--min-turnover-ratio', type=float, default=0.0, help='最小换手率过滤(%%)')
    parser.add_argument('--max-total-mv-yi', type=float, default=1200, help='总市值上限(亿)')
    parser.add_argument('--max-circ-mv-yi', type=float, default=800, help='流通市值上限(亿)')
    parser.add_argument('--allow-mainboard-60', action='store_true', help='允许60主板在满足阈值时入选')
    parser.add_argument('--output-json', default='', help='把结果额外写入指定 JSON 文件')
    parser.add_argument('--json', action='store_true', help='输出 JSON')
    args = parser.parse_args()

    candidates, rejected_largecap, rejected_live, source, live_items = first_round_candidates(
        top_n=args.top_n,
        min_change_pct=args.min_change_pct,
        min_amount_yi=args.min_amount_yi,
        pick_count=args.pick_count,
        max_total_mv_yi=args.max_total_mv_yi,
        max_circ_mv_yi=args.max_circ_mv_yi,
        allow_mainboard_60=args.allow_mainboard_60,
        min_turnover_ratio=args.min_turnover_ratio,
    )
    passed, partial, failed = second_round_filter(candidates)
    true_leaders, strong_followers, pseudo_strong = classify_trading_roles(passed, partial, failed)
    watchlist = build_watchlist(true_leaders, strong_followers)
    chinese_summary = build_chinese_summary(true_leaders, strong_followers, pseudo_strong, watchlist)

    payload = {
        'plugin': PLUGIN_NAME,
        'version': 'v4',
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'date': args.date,
        'strategy': '优先东方财富实时全市场 -> 再用新浪全市场涨幅榜 -> 剔除大票/权重 -> 保留中小盘/创业板/次新/弹性票 -> 近3日量价 + 5日线过滤',
        'market_scan_source': source,
        'top_n': args.top_n,
        'pick_count': args.pick_count,
        'min_change_pct': args.min_change_pct,
        'min_amount_yi': args.min_amount_yi,
        'min_turnover_ratio': args.min_turnover_ratio,
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
        'chinese_summary': chinese_summary,
        'rejected_largecap': rejected_largecap,
        'rejected_live': rejected_live,
        'data_sources': {
            'realtime_scan': source,
            'primary': '东方财富实时全市场',
            'secondary': '新浪全市场涨幅榜',
            'daily_filter': '腾讯历史K线(akshare)',
            'fallback': '新浪/腾讯候选池fallback + V6内置中小盘池',
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
