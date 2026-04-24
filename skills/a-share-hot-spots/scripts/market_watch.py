#!/usr/bin/env python3
import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from pytdx.hq import TdxHq_API

ENABLE_EASTMONEY = False

BASE_DIR = Path(__file__).resolve().parent.parent
SHARED_POOL_DIR = BASE_DIR.parent / 'shared_a_share_pool'
import sys
sys.path.insert(0, str(SHARED_POOL_DIR.parent))
from shared_a_share_pool import UniverseFilters, load_shared_universe, names_from_universe

NAME_MAP_PATH = BASE_DIR / "references" / "name_map.csv"
AUCTION_SCANNER_DIR = BASE_DIR.parent / "auction_915_925_smooth_scanner"
AUCTION_UNIVERSE_PATH = AUCTION_SCANNER_DIR / "outputs" / "sz_mainboard_00_universe.json"
AUCTION_SOURCE_NAME = "pytdx_snapshot"

DEFAULT_TDX_SERVERS = [
    ("183.60.224.178", 7709),
    ("39.108.28.120", 7709),
    ("119.147.212.81", 7709),
]


def load_name_map() -> dict:
    mapping = {}
    if NAME_MAP_PATH.exists():
        with NAME_MAP_PATH.open("r", encoding="utf-8") as f:
            for row in csv.reader(f):
                if len(row) >= 2:
                    mapping[row[0].strip()] = row[1].strip()
    return mapping


def load_code_name_map() -> dict:
    direct = load_name_map()
    reverse = {}
    for name, code in direct.items():
        reverse[code.strip()] = name.strip()
    return reverse


def safe_float(value, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if not text or text in {"-", "--", "None", "null", "NULL", "N/A"}:
        return default
    try:
        return float(text)
    except Exception:
        return default


def normalize_code(code: str):
    code = str(code).strip().upper()
    if code.startswith("SH") or code.startswith("SZ"):
        return code[:2].lower(), ''.join(ch for ch in code[2:] if ch.isdigit())
    digits = ''.join(ch for ch in code if ch.isdigit())
    if digits.startswith(("60", "68", "51", "58", "11")):
        return "sh", digits
    if digits.startswith(("00", "30", "12", "13", "15", "16")):
        return "sz", digits
    return "sh", digits


def market_for_code(code: str) -> int:
    _, digits = normalize_code(code)
    if digits.startswith(("00", "001", "002", "003", "30", "12", "13", "15", "16")):
        return 0
    return 1


def _connect_tdx() -> tuple[TdxHq_API, tuple[str, int]]:
    last_error = None
    for host, port in DEFAULT_TDX_SERVERS:
        api = TdxHq_API()
        try:
            if api.connect(host, port, time_out=1):
                return api, (host, port)
        except Exception as e:
            last_error = e
        try:
            api.disconnect()
        except Exception:
            pass
    raise RuntimeError(f"pytdx connect failed: {last_error}")


def _fetch_quotes(symbols: list[str]) -> list[dict]:
    api, _server = _connect_tdx()
    try:
        req = [(market_for_code(code), normalize_code(code)[1]) for code in symbols]
        rows = api.get_security_quotes(req) or []
        return [dict(x) for x in rows]
    finally:
        try:
            api.disconnect()
        except Exception:
            pass


def _bars_to_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    if 'datetime' in df.columns:
        df['date'] = pd.to_datetime(df['datetime'], errors='coerce')
    elif {'year', 'month', 'day'}.issubset(df.columns):
        year_series = pd.to_numeric(df['year'], errors='coerce').fillna(datetime.now().year).astype(int)
        month_series = pd.to_numeric(df['month'], errors='coerce').fillna(1).astype(int)
        day_series = pd.to_numeric(df['day'], errors='coerce').fillna(1).astype(int)
        df['date'] = pd.to_datetime({
            'year': year_series,
            'month': month_series,
            'day': day_series,
        }, errors='coerce')
    else:
        raise RuntimeError(f'pytdx bars missing date columns: {list(df.columns)}')
    if 'vol' in df.columns and 'volume' not in df.columns:
        df['volume'] = df['vol']
    return df


def fetch_daily_df_tdx(code: str, bars: int = 30) -> pd.DataFrame:
    market = market_for_code(code)
    _, digits = normalize_code(code)
    api, _server = _connect_tdx()
    try:
        rows = api.get_security_bars(9, market, digits, 0, bars) or []
    finally:
        try:
            api.disconnect()
        except Exception:
            pass
    df = _bars_to_df([dict(x) for x in rows])
    if df.empty:
        raise RuntimeError('pytdx daily bars empty')
    for col in ['open', 'close', 'high', 'low', 'volume']:
        if col not in df.columns:
            raise RuntimeError(f'pytdx daily bars missing {col}')
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['date', 'close', 'volume']).sort_values('date').reset_index(drop=True)
    df['ma5'] = df['close'].rolling(5).mean()
    return df


def fetch_stock(code: str) -> dict:
    prefix, digits = normalize_code(code)
    rows = _fetch_quotes([digits])
    if not rows:
        return {"error": f"未拿到 {code} 行情", "symbol": f"{prefix}{digits}"}
    row = rows[0]
    code_name_map = load_code_name_map()
    prev_close = safe_float(row.get('last_close'))
    current = safe_float(row.get('price'))
    change = current - prev_close
    change_pct = (change / prev_close * 100) if prev_close else 0
    return {
        "symbol": f"{prefix}{digits}",
        "code": digits,
        "name": code_name_map.get(digits, digits),
        "current": round(current, 2),
        "change": round(change, 2),
        "change_pct": round(change_pct, 2),
        "open": round(safe_float(row.get('open')), 2),
        "high": round(safe_float(row.get('high')), 2),
        "low": round(safe_float(row.get('low')), 2),
        "prev_close": round(prev_close, 2),
        "volume_lot": int(safe_float(row.get('vol'))),
        "amount_yi": round(safe_float(row.get('amount')) / 1e8, 2),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": str(row.get('servertime', '')),
        "source": "pytdx/通达信协议",
        "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def fetch_monthly_klines(code: str, months: int = 48) -> list:
    market = market_for_code(code)
    _, digits = normalize_code(code)
    api, _server = _connect_tdx()
    try:
        rows = api.get_security_bars(6, market, digits, 0, months) or []
    finally:
        try:
            api.disconnect()
        except Exception:
            pass
    df = _bars_to_df([dict(x) for x in rows])
    if df.empty:
        return []
    for col in ['open', 'close', 'high', 'low']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    vol_col = 'volume' if 'volume' in df.columns else 'vol'
    df[vol_col] = pd.to_numeric(df[vol_col], errors='coerce')
    df = df.dropna(subset=['date', 'open', 'close', 'high', 'low', vol_col]).sort_values('date')
    out = []
    for _, row in df.tail(months).iterrows():
        out.append({
            "date": row["date"].strftime("%Y-%m-%d"),
            "open": float(row["open"]),
            "close": float(row["close"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "volume": float(row[vol_col]),
        })
    return out


def analyze_strategy(code: str) -> dict:
    stock = fetch_stock(code)
    if stock.get("error"):
        return {"error": stock["error"]}
    try:
        monthly = fetch_monthly_klines(code, 48)
    except Exception as e:
        return {"error": f"月线接口暂时失败：{e}"}
    if len(monthly) < 24:
        return {"error": "月线数据不足，无法做策略判断"}

    recent4 = monthly[-4:]
    prev24 = monthly[-28:-4] if len(monthly) >= 28 else monthly[:-4]
    base_vol_avg = sum(x["volume"] for x in prev24) / len(prev24) if prev24 else 0
    recent_vol_flags = [x["volume"] > base_vol_avg * 1.3 for x in recent4] if base_vol_avg else [False] * len(recent4)
    volume_pass = sum(recent_vol_flags) >= 2

    closes = [x["close"] for x in monthly]
    min_close = min(closes)
    max_close = max(closes)
    current_close = closes[-1]
    position = (current_close - min_close) / (max_close - min_close) if max_close > min_close else 0
    bottom_zone_pass = position <= 0.40

    trend_up_pass = recent4[-1]["close"] > recent4[0]["close"]

    width_ratio = (max_close - min_close) / min_close if min_close > 0 else 999
    sideways_pass = width_ratio <= 1.5 and position <= 0.5

    score = sum([volume_pass, bottom_zone_pass, trend_up_pass, sideways_pass])
    verdict = "符合" if score >= 4 else ("部分符合" if score >= 2 else "不符合")

    reason = []
    reason.append("最近4个月出现底部放量" if volume_pass else "最近4个月放量不够明显")
    reason.append("当前仍处长期区间下部" if bottom_zone_pass else "当前价格已不算明显底部区")
    reason.append("最近4个月收盘重心上移" if trend_up_pass else "最近4个月尚未走出明显抬升")
    reason.append("近4年更像横盘吸筹结构" if sideways_pass else "近4年波动区间偏大，未必是典型底部横盘")

    return {
        "name": stock["name"],
        "symbol": stock["symbol"],
        "verdict": verdict,
        "score": score,
        "rules": {
            "volume_pass": volume_pass,
            "bottom_zone_pass": bottom_zone_pass,
            "trend_up_pass": trend_up_pass,
            "sideways_pass": sideways_pass,
        },
        "metrics": {
            "base_vol_avg": round(base_vol_avg, 2),
            "recent_4m_volumes": [round(x["volume"], 2) for x in recent4],
            "position_in_4y_range": round(position, 3),
            "range_width_ratio": round(width_ratio, 3),
            "recent_4m_close": [x["close"] for x in recent4],
        },
        "summary": "；".join(reason),
    }


def fetch_index() -> list:
    symbols = "s_sh000001,s_sz399001,s_sz399006,s_sh000688"
    raw = fetch_text(f"http://hq.sinajs.cn/list={symbols}")
    mapping = {
        "s_sh000001": "上证指数",
        "s_sz399001": "深证成指",
        "s_sz399006": "创业板指",
        "s_sh000688": "科创50",
    }
    out = []
    for sym, name in mapping.items():
        m = re.search(rf'hq_str_{re.escape(sym)}="([^"]*)"', raw)
        if not m:
            continue
        p = m.group(1).split(",")
        if len(p) < 5:
            continue
        out.append({
            "name": p[0] or name,
            "current": float(p[1]),
            "change": float(p[2]),
            "change_pct": float(p[3]),
            "amount_yi": round(float(p[5]) / 1e8, 2) if len(p) > 5 and p[5] else 0,
            "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "新浪财经",
        })
    return out


def load_shared_pool(limit: int | None = None) -> tuple[dict, dict[str, str]]:
    filters = UniverseFilters(
        allow_markets=('sz',),
        include_prefixes=('00',),
        exclude_prefixes=('300', '301', '688', '689', '8', '4'),
        exclude_st=True,
        exclude_delisting=True,
        min_listed_days=60,
        limit=limit,
    )
    universe = load_shared_universe(filters=filters)
    return universe, names_from_universe(universe)


def load_auction_universe() -> list[dict]:
    universe, _name_map = load_shared_pool(limit=2000)
    return universe.get('selected', [])


def auction_candidates(limit: int = 30) -> list[dict]:
    universe, shared_name_map = load_shared_pool(limit=limit)
    selected = universe.get('selected', [])
    if not selected:
        return []
    out = []
    for item in selected[:limit]:
        code = str(item.get("code") or "").strip()
        name = shared_name_map.get(code, str(item.get("name") or code).strip() or code)
        if not code:
            continue
        symbol = f"sz{code}" if not code.startswith(("sh", "sz")) else code.lower()
        out.append({
            "symbol": symbol,
            "code": code.replace("sh", "").replace("sz", ""),
            "name": name,
        })
    return out


def fetch_auction_preopen_snapshot(limit: int = 30) -> list[dict]:
    candidates = auction_candidates(limit=limit)
    out = []
    for item in candidates:
        code = item["code"]
        try:
            df = ak.stock_zh_a_hist_pre_min_em(
                symbol=code,
                start_time="09:15:00",
                end_time="09:25:00",
            )
        except Exception:
            continue
        if df is None or getattr(df, "empty", True):
            continue

        rename_map = {
            "时间": "time",
            "日期时间": "time",
            "成交价": "price",
            "价格": "price",
            "开盘": "price",
            "成交量": "volume",
            "成交额": "amount",
        }
        df = df.copy()
        df.columns = [rename_map.get(str(c), str(c)) for c in list(df.columns)]
        if "price" not in df.columns:
            continue

        prices = []
        amounts = []
        for _, row in df.iterrows():
            try:
                prices.append(float(row.get("price")))
            except Exception:
                continue
            try:
                amounts.append(float(row.get("amount") or 0))
            except Exception:
                amounts.append(0.0)
        if len(prices) < 2:
            continue

        first_price = prices[0]
        last_price = prices[-1]
        change = last_price - first_price
        change_pct = (change / first_price * 100) if first_price else 0.0
        amount_yi = round(sum(amounts) / 1e8, 2)
        out.append({
            "symbol": item["symbol"],
            "code": code,
            "name": item["name"],
            "current": round(last_price, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "volume_lot": 0,
            "amount_yi": amount_yi,
            "source": AUCTION_SOURCE_NAME,
            "data_granularity": "minute_agg",
        })
    out.sort(key=lambda x: (x.get("change_pct", 0), x.get("amount_yi", 0)), reverse=True)
    return out


def infer_auction_hot_sectors(items: list[dict]) -> list[dict]:
    if not items:
        return []
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in items:
        code = str(row.get("code") or "")
        if code.startswith("000"):
            sector = "深市主板00竞价强势"
        elif code.startswith("001"):
            sector = "深市主板001竞价强势"
        elif code.startswith("002"):
            sector = "中小盘竞价强势"
        else:
            sector = "竞价强势观察"
        groups[sector].append(row)

    out = []
    for sector, rows in groups.items():
        rows = sorted(rows, key=lambda x: (x.get("change_pct", 0), x.get("amount_yi", 0)), reverse=True)
        leader = rows[0]
        avg_change = sum(x.get("change_pct", 0) for x in rows) / len(rows)
        out.append({
            "name": sector,
            "change_pct": round(avg_change, 2),
            "leading_stock": leader.get("name", ""),
            "leading_change_pct": round(leader.get("change_pct", 0), 2),
            "amount_yi": round(sum(x.get("amount_yi", 0) for x in rows), 2),
            "source": f"{AUCTION_SOURCE_NAME}/sector_infer",
        })
    out.sort(key=lambda x: (x.get("change_pct", 0), x.get("amount_yi", 0)), reverse=True)
    return out[:5]


def infer_auction_industry_sectors(items: list[dict]) -> list[dict]:
    return infer_auction_hot_sectors(items)


def fetch_hot_sectors_tx_fallback() -> list:
    candidates = fetch_hot_stocks_tx_fallback()
    groups = {
        '算力/AI': ['中芯国际', '寒武纪', '工业富联'],
        '金融科技': ['东方财富', '中国平安', '中信证券'],
        '新能源': ['宁德时代', '隆基绿能'],
        '资源周期': ['紫金矿业'],
        '消费医药': ['药明康德', '中国中免', '贵州茅台', '美的集团'],
    }
    out = []
    for sector, names in groups.items():
        rows = [x for x in candidates if _decode_possible_garbled(x.get('name', '')) in names]
        if not rows:
            continue
        rows = sorted(rows, key=lambda x: x.get('change_pct', 0), reverse=True)
        avg_change = sum(x.get('change_pct', 0) for x in rows) / len(rows)
        leader = rows[0]
        out.append({
            'name': sector,
            'change_pct': round(avg_change, 2),
            'leading_stock': leader.get('name', ''),
            'leading_change_pct': leader.get('change_pct', 0),
            'amount_yi': round(sum(x.get('amount_yi', 0) for x in rows), 2),
            'source': '腾讯/新浪板块fallback',
        })
    out.sort(key=lambda x: (x.get('change_pct', 0), x.get('amount_yi', 0)), reverse=True)
    return out[:5]


def fetch_hot_sectors() -> list:
    auction_items = fetch_auction_preopen_snapshot(limit=30)
    if auction_items:
        inferred = infer_auction_hot_sectors(auction_items)
        if inferred:
            return inferred

    url = (
        "http://push2.eastmoney.com/api/qt/clist/get"
        "?pn=1&pz=20&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281"
        "&fltt=2&invt=2&fid=f3&fs=m:90+t:2+f:!50"
        "&fields=f3,f14,f20,f128,f136"
    )
    if ENABLE_EASTMONEY:
        try:
            raw = fetch_text(url, referer="https://www.eastmoney.com")
            obj = json.loads(raw)
            diff = ((obj.get("data") or {}).get("diff") or [])
            out = []
            for item in diff:
                out.append({
                    "name": item.get("f14", ""),
                    "change_pct": round(safe_float(item.get("f3", 0)), 2),
                    "leading_stock": item.get("f128", ""),
                    "leading_change_pct": round(safe_float(item.get("f136", 0)), 2),
                    "amount_yi": round(safe_float(item.get("f20", 0)) / 1e8, 2),
                    "source": "东方财富",
                })
            if out:
                return out
        except Exception:
            pass
    return fetch_hot_sectors_tx_fallback()


def fetch_hot_stocks_tx_fallback() -> list:
    mapping = load_name_map()
    names = list(mapping.keys())[:20]
    out = []
    for name in names:
        code = mapping.get(name, "")
        if not code:
            continue
        try:
            stock = fetch_stock(code)
        except Exception:
            continue
        if stock.get("error"):
            continue
        out.append({
            "symbol": stock.get("symbol", ""),
            "name": stock.get("name", name),
            "current": stock.get("current", 0),
            "change_pct": stock.get("change_pct", 0),
            "change": stock.get("change", 0),
            "volume_lot": stock.get("volume_lot", 0),
            "amount_yi": stock.get("amount_yi", 0),
            "source": "腾讯/新浪候选池fallback",
        })
    out.sort(key=lambda x: (x.get("change_pct", 0), x.get("amount_yi", 0)), reverse=True)
    return out[:15]


def fetch_hot_stocks() -> list:
    auction_items = fetch_auction_preopen_snapshot(limit=30)
    if auction_items:
        return auction_items[:15]

    url = (
        "http://push2.eastmoney.com/api/qt/clist/get"
        "?pn=1&pz=15&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281"
        "&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"
        "&fields=f12,f14,f2,f3,f4,f5,f6"
    )
    if ENABLE_EASTMONEY:
        try:
            raw = fetch_text(url, referer="https://quote.eastmoney.com")
            obj = json.loads(raw)
            diff = ((obj.get("data") or {}).get("diff") or [])
            out = []
            for item in diff:
                code = str(item.get("f12", ""))
                market = "sh" if code.startswith(("60", "68")) else "sz"
                out.append({
                    "symbol": f"{market}{code}",
                    "name": item.get("f14", ""),
                    "current": round(safe_float(item.get("f2", 0)), 2),
                    "change_pct": round(safe_float(item.get("f3", 0)), 2),
                    "change": round(safe_float(item.get("f4", 0)), 2),
                    "volume_lot": int(safe_float(item.get("f5", 0))),
                    "amount_yi": round(safe_float(item.get("f6", 0)) / 1e8, 2),
                    "source": "东方财富",
                })
            if out:
                return out
        except Exception:
            pass
    return fetch_hot_stocks_tx_fallback()


def fetch_industry_sectors() -> list:
    auction_items = fetch_auction_preopen_snapshot(limit=30)
    if auction_items:
        inferred = infer_auction_industry_sectors(auction_items)
        if inferred:
            return inferred

    url = (
        "http://push2.eastmoney.com/api/qt/clist/get"
        "?pn=1&pz=20&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281"
        "&fltt=2&invt=2&fid=f3&fs=m:90+t:3+f:!50"
        "&fields=f3,f14,f20,f128,f136"
    )
    raw = fetch_text(url, referer="https://quote.eastmoney.com")
    obj = json.loads(raw)
    diff = ((obj.get("data") or {}).get("diff") or [])
    out = []
    for item in diff:
        out.append({
            "name": item.get("f14", ""),
            "change_pct": round(safe_float(item.get("f3", 0)), 2),
            "leading_stock": item.get("f128", ""),
            "leading_change_pct": round(safe_float(item.get("f136", 0)), 2),
            "amount_yi": round(safe_float(item.get("f20", 0)) / 1e8, 2),
        })
    return out


def fetch_limit_up() -> list:
    items = fetch_hot_stocks()
    return [x for x in items if x.get("change_pct", 0) >= 9.8]


def fmt_stock(d: dict) -> str:
    if d.get("error"):
        return f"失败：{d['error']}"
    sign = "+" if d["change"] >= 0 else ""
    direction = "涨" if d["change"] >= 0 else "跌"
    return "\n".join([
        f"{direction} {d['name']}（{d['symbol'].upper()}）",
        f"当前价：{d['current']} 元",
        f"涨跌：{sign}{d['change']}（{sign}{d['change_pct']}%）",
        f"今开：{d['open']}  最高：{d['high']}  最低：{d['low']}  昨收：{d['prev_close']}",
        f"成交量：{d['volume_lot']:,} 手  成交额：{d['amount_yi']} 亿",
        f"来源：{d['source']} | 时间：{d.get('date','')} {d.get('time','')}"
    ])


def fmt_index(items: list) -> str:
    if not items:
        return "失败：未拿到指数数据"
    lines = ["A股主要指数"]
    for d in items:
        sign = "+" if d["change"] >= 0 else ""
        direction = "涨" if d["change"] >= 0 else "跌"
        lines.append(f"{direction} {d['name']}：{d['current']:.2f}  {sign}{d['change']:+.2f}（{sign}{d['change_pct']}%）  成交额 {d['amount_yi']} 亿")
    lines.append(f"更新时间：{items[0]['fetch_time']}")
    return "\n".join(lines)


def fmt_sectors(items: list) -> str:
    if not items:
        return "失败：未拿到热点板块数据"
    lines = ["A股热点板块（TOP20）"]
    for i, d in enumerate(items, 1):
        sign = "+" if d["change_pct"] >= 0 else ""
        lead_sign = "+" if d["leading_change_pct"] >= 0 else ""
        lines.append(f"{i:02d}. {d['name']}  {sign}{d['change_pct']}%  龙头：{d['leading_stock']}（{lead_sign}{d['leading_change_pct']}%）  成交额：{d['amount_yi']}亿")
    return "\n".join(lines)


def fmt_hot_stocks(items: list) -> str:
    if not items:
        return "失败：未拿到热门股数据"
    lines = ["A股热门股（按涨幅排序，TOP15）"]
    for i, d in enumerate(items, 1):
        sign = "+" if d["change_pct"] >= 0 else ""
        lines.append(f"{i:02d}. {d['name']}（{d['symbol'].upper()}） {d['current']}元  {sign}{d['change_pct']}%  成交额 {d['amount_yi']}亿")
    return "\n".join(lines)


def fmt_industry_sectors(items: list) -> str:
    if not items:
        return "失败：未拿到行业板块数据"
    lines = ["A股行业板块（TOP20）"]
    for i, d in enumerate(items, 1):
        sign = "+" if d["change_pct"] >= 0 else ""
        lead_sign = "+" if d["leading_change_pct"] >= 0 else ""
        lines.append(f"{i:02d}. {d['name']}  {sign}{d['change_pct']}%  龙头：{d['leading_stock']}（{lead_sign}{d['leading_change_pct']}%）  成交额：{d['amount_yi']}亿")
    return "\n".join(lines)


def fmt_limit_up(items: list) -> str:
    if not items:
        return "今天未筛到明显涨停/强势股"
    lines = ["A股涨停/强势股"]
    for i, d in enumerate(items, 1):
        lines.append(f"{i:02d}. {d['name']}（{d['symbol'].upper()}） {d['current']}元  +{d['change_pct']}%  成交额 {d['amount_yi']}亿")
    return "\n".join(lines)


def fmt_summary(indexes: list, sectors: list, stocks: list) -> str:
    lines = [fmt_index(indexes), "", "热点前三："]
    for i, d in enumerate(sectors[:3], 1):
        sign = "+" if d["change_pct"] >= 0 else ""
        lines.append(f"{i}. {d['name']} {sign}{d['change_pct']}%｜龙头 {d['leading_stock']}")
    lines += ["", "热门股前三："]
    for i, d in enumerate(stocks[:3], 1):
        sign = "+" if d["change_pct"] >= 0 else ""
        lines.append(f"{i}. {d['name']} {d['current']}元｜{sign}{d['change_pct']}%")
    return "\n".join(lines)


def fmt_brief(indexes: list, sectors: list, stocks: list) -> str:
    if not indexes:
        return "盘面短播报：暂未拿到指数数据"
    idx = indexes[0]
    idx_sign = "+" if idx["change_pct"] >= 0 else ""
    parts = [f"盘面短播报：上证 {idx['current']:.2f}（{idx_sign}{idx['change_pct']}%）"]
    if sectors:
        top_sector = sectors[0]
        sec_sign = "+" if top_sector["change_pct"] >= 0 else ""
        parts.append(f"最强板块 {top_sector['name']}（{sec_sign}{top_sector['change_pct']}%）")
        if top_sector.get("leading_stock"):
            parts.append(f"龙头 {top_sector['leading_stock']}")
    if stocks:
        top_stock = stocks[0]
        stk_sign = "+" if top_stock["change_pct"] >= 0 else ""
        parts.append(f"强势股 {top_stock['name']}（{stk_sign}{top_stock['change_pct']}%）")
    return "｜".join(parts)


def fmt_sector_brief(sectors: list, industries: list) -> str:
    lines = ["板块联动摘要"]
    if sectors:
        lines.append("概念热点：")
        for i, d in enumerate(sectors[:5], 1):
            sign = "+" if d["change_pct"] >= 0 else ""
            lines.append(f"{i}. {d['name']} {sign}{d['change_pct']}%｜龙头 {d['leading_stock']}")
    if industries:
        lines.append("")
        lines.append("行业热点：")
        for i, d in enumerate(industries[:5], 1):
            sign = "+" if d["change_pct"] >= 0 else ""
            lines.append(f"{i}. {d['name']} {sign}{d['change_pct']}%｜龙头 {d['leading_stock']}")
    return "\n".join(lines)


def fmt_strategy(result: dict) -> str:
    if result.get("error"):
        return f"策略检测失败：{result['error']}"
    lines = [
        f"策略检测：{result['name']}（{result['symbol'].upper()}）",
        f"结论：{result['verdict']}（评分 {result['score']}/4）",
        f"- 最近4个月放量：{'通过' if result['rules']['volume_pass'] else '未通过'}",
        f"- 当前位于4年区间底部：{'通过' if result['rules']['bottom_zone_pass'] else '未通过'}",
        f"- 最近4个月收盘抬升：{'通过' if result['rules']['trend_up_pass'] else '未通过'}",
        f"- 近4年横盘吸筹特征：{'通过' if result['rules']['sideways_pass'] else '未通过'}",
        f"区间位置：{result['metrics']['position_in_4y_range']}",
        f"区间宽度比：{result['metrics']['range_width_ratio']}",
        f"最近4个月收盘：{result['metrics']['recent_4m_close']}",
        f"最近4个月量能：{result['metrics']['recent_4m_volumes']}",
        f"说明：{result['summary']}",
    ]
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description="A股实时盯盘")
    parser.add_argument("--code", nargs="+", help="股票代码，可多个")
    parser.add_argument("--name", nargs="+", help="中文股票名，可多个")
    parser.add_argument("--index", action="store_true", help="查主要指数")
    parser.add_argument("--hot-sectors", action="store_true", help="查热点板块")
    parser.add_argument("--hot-stocks", action="store_true", help="查热门股")
    parser.add_argument("--industry-sectors", action="store_true", help="查行业板块")
    parser.add_argument("--limit-up", action="store_true", help="查涨停/强势股")
    parser.add_argument("--summary", action="store_true", help="查盘面摘要")
    parser.add_argument("--brief", action="store_true", help="查短播报")
    parser.add_argument("--sector-brief", action="store_true", help="查板块联动摘要")
    parser.add_argument("--strategy-check", help="按 V5 策略检测单只股票代码")
    parser.add_argument("--strategy-name", help="按 V5 策略检测单只中文股票名")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    if args.summary:
        indexes = fetch_index()
        sectors = fetch_hot_sectors()
        stocks = fetch_hot_stocks()
        if args.json:
            print(json.dumps({"indexes": indexes, "hot_sectors": sectors[:3], "hot_stocks": stocks[:3]}, ensure_ascii=False, indent=2))
        else:
            print(fmt_summary(indexes, sectors, stocks))
        return

    if args.strategy_check:
        result = analyze_strategy(args.strategy_check)
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else fmt_strategy(result))
        return

    if args.strategy_name:
        resolved = resolve_names([args.strategy_name])
        result = analyze_strategy(resolved[0])
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else fmt_strategy(result))
        return

    if args.brief:
        indexes = fetch_index()
        sectors = fetch_hot_sectors()
        stocks = fetch_hot_stocks()
        if args.json:
            print(json.dumps({"indexes": indexes[:1], "hot_sectors": sectors[:1], "hot_stocks": stocks[:1]}, ensure_ascii=False, indent=2))
        else:
            print(fmt_brief(indexes, sectors, stocks))
        return

    if args.sector_brief:
        sectors = fetch_hot_sectors()
        industries = fetch_industry_sectors()
        if args.json:
            print(json.dumps({"concept_sectors": sectors[:5], "industry_sectors": industries[:5]}, ensure_ascii=False, indent=2))
        else:
            print(fmt_sector_brief(sectors, industries))
        return

    if args.index:
        data = fetch_index()
        print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else fmt_index(data))
        return

    if args.hot_sectors:
        data = fetch_hot_sectors()
        print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else fmt_sectors(data))
        return

    if args.hot_stocks:
        data = fetch_hot_stocks()
        print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else fmt_hot_stocks(data))
        return

    if args.industry_sectors:
        data = fetch_industry_sectors()
        print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else fmt_industry_sectors(data))
        return

    if args.limit_up:
        data = fetch_limit_up()
        print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else fmt_limit_up(data))
        return

    if args.name:
        resolved = resolve_names(args.name)
        data = [fetch_stock(c) for c in resolved]
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            for item in data:
                print(fmt_stock(item))
                print()
        return

    if args.code:
        data = [fetch_stock(c) for c in args.code]
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            for item in data:
                print(fmt_stock(item))
                print()
        return

    parser.print_help()


if __name__ == "__main__":
    main()
