#!/usr/bin/env python3
import argparse
import csv
import json
import re
import urllib.request
from datetime import datetime
from pathlib import Path

import akshare as ak
ENABLE_EASTMONEY = False


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://finance.sina.com.cn",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

BASE_DIR = Path(__file__).resolve().parent.parent
NAME_MAP_PATH = BASE_DIR / "references" / "name_map.csv"


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


def fetch_text(url: str, referer: str | None = None, timeout: int = 10) -> str:
    headers = dict(HEADERS)
    if referer:
        headers["Referer"] = referer
    last_error = None
    for _ in range(3):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                charset = "gbk" if "sina" in url or "sinajs" in url else "utf-8"
                return raw.decode(charset, errors="replace")
        except Exception as e:
            last_error = e
    raise last_error


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
    code = code.strip().upper()
    if code.startswith("SH") or code.startswith("SZ"):
        return code[:2].lower(), re.sub(r"\D", "", code[2:])
    digits = re.sub(r"\D", "", code)
    if digits.startswith(("60", "68", "51", "58", "11")):
        return "sh", digits
    if digits.startswith(("00", "30", "12", "13", "15", "16")):
        return "sz", digits
    return "sh", digits


def resolve_names(names: list[str]) -> list[str]:
    mapping = load_name_map()
    resolved = []
    for name in names:
        code = mapping.get(name.strip())
        if code:
            resolved.append(code)
        else:
            resolved.append(f"UNKNOWN:{name}")
    return resolved


def _decode_possible_garbled(text: str) -> str:
    if not text:
        return text
    try:
        if '�' in text or any(ch in text for ch in ['����', '��', '�']):
            return text.encode('latin1', errors='ignore').decode('gbk', errors='ignore') or text
    except Exception:
        pass
    return text


def fetch_stock(code: str) -> dict:
    if code.startswith("UNKNOWN:"):
        return {"error": f"暂不认识这个股票名：{code.split(':', 1)[1]}", "symbol": code}
    prefix, digits = normalize_code(code)
    symbol = f"{prefix}{digits}"
    raw = fetch_text(f"http://hq.sinajs.cn/list={symbol}")
    m = re.search(r'"([^"]*)"', raw)
    if not m:
        return {"error": f"未拿到 {code} 行情", "symbol": symbol}
    parts = m.group(1).split(",")
    if len(parts) < 32 or not parts[0]:
        return {"error": f"未拿到 {code} 行情", "symbol": symbol}
    prev_close = float(parts[2] or 0)
    current = float(parts[3] or 0)
    change = current - prev_close
    change_pct = (change / prev_close * 100) if prev_close else 0
    code_name_map = load_code_name_map()
    preferred_name = code_name_map.get(digits) or _decode_possible_garbled(parts[0])
    return {
        "symbol": symbol,
        "code": digits,
        "name": preferred_name,
        "current": round(current, 2),
        "change": round(change, 2),
        "change_pct": round(change_pct, 2),
        "open": round(float(parts[1] or 0), 2),
        "high": round(float(parts[4] or 0), 2),
        "low": round(float(parts[5] or 0), 2),
        "prev_close": round(prev_close, 2),
        "volume_lot": int(float(parts[8] or 0)),
        "amount_yi": round(float(parts[9] or 0) / 1e8, 2),
        "date": parts[30],
        "time": parts[31],
        "source": "新浪财经",
        "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def fetch_monthly_klines(code: str, months: int = 48) -> list:
    prefix, digits = normalize_code(code)
    symbol = f"{prefix}{digits}"
    try:
        df = ak.stock_zh_a_hist_tx(symbol=symbol, start_date="20190101", end_date="20500101", adjust="")
    except Exception as e:
        raise RuntimeError(f"腾讯历史接口失败: {e}")

    if df is None or df.empty:
        return []

    rename_map = {}
    for col in df.columns:
        c = str(col).strip()
        if c in ["date", "日期"]:
            rename_map[col] = "date"
        elif c in ["open", "开盘"]:
            rename_map[col] = "open"
        elif c in ["close", "收盘"]:
            rename_map[col] = "close"
        elif c in ["high", "最高"]:
            rename_map[col] = "high"
        elif c in ["low", "最低"]:
            rename_map[col] = "low"
        elif c in ["amount", "成交量", "volume"]:
            rename_map[col] = "amount"
    df = df.rename(columns=rename_map)

    required = ["date", "open", "close", "high", "low", "amount"]
    if not all(col in df.columns for col in required):
        raise RuntimeError(f"腾讯历史接口字段异常: {list(df.columns)}")

    df = df[required].copy()
    df["date"] = pd.to_datetime(df["date"])
    for col in ["open", "close", "high", "low", "amount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna().sort_values("date")
    if df.empty:
        return []

    monthly_df = (
        df.set_index("date")
          .resample("ME")
          .agg({
              "open": "first",
              "close": "last",
              "high": "max",
              "low": "min",
              "amount": "sum",
          })
          .dropna()
          .reset_index()
    )

    out = []
    for _, row in monthly_df.tail(months).iterrows():
        out.append({
            "date": row["date"].strftime("%Y-%m-%d"),
            "open": float(row["open"]),
            "close": float(row["close"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "volume": float(row["amount"]),
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
