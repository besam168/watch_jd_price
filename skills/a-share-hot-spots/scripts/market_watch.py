#!/usr/bin/env python3
import argparse
import csv
import json
import re
import urllib.request
from datetime import datetime
from pathlib import Path

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


def fetch_text(url: str, referer: str | None = None, timeout: int = 10) -> str:
    headers = dict(HEADERS)
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        charset = "gbk" if "sina" in url or "sinajs" in url else "utf-8"
        return raw.decode(charset, errors="replace")


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
    return {
        "symbol": symbol,
        "name": parts[0],
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


def fetch_hot_sectors() -> list:
    url = (
        "http://push2.eastmoney.com/api/qt/clist/get"
        "?pn=1&pz=20&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281"
        "&fltt=2&invt=2&fid=f3&fs=m:90+t:2+f:!50"
        "&fields=f3,f14,f20,f128,f136"
    )
    raw = fetch_text(url, referer="https://www.eastmoney.com")
    obj = json.loads(raw)
    diff = ((obj.get("data") or {}).get("diff") or [])
    out = []
    for item in diff:
        out.append({
            "name": item.get("f14", ""),
            "change_pct": round(float(item.get("f3", 0) or 0), 2),
            "leading_stock": item.get("f128", ""),
            "leading_change_pct": round(float(item.get("f136", 0) or 0), 2),
            "amount_yi": round(float(item.get("f20", 0) or 0) / 1e8, 2),
        })
    return out


def fetch_hot_stocks() -> list:
    url = (
        "http://push2.eastmoney.com/api/qt/clist/get"
        "?pn=1&pz=15&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281"
        "&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"
        "&fields=f12,f14,f2,f3,f4,f5,f6"
    )
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
            "current": round(float(item.get("f2", 0) or 0), 2),
            "change_pct": round(float(item.get("f3", 0) or 0), 2),
            "change": round(float(item.get("f4", 0) or 0), 2),
            "volume_lot": int(float(item.get("f5", 0) or 0)),
            "amount_yi": round(float(item.get("f6", 0) or 0) / 1e8, 2),
        })
    return out


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
            "change_pct": round(float(item.get("f3", 0) or 0), 2),
            "leading_stock": item.get("f128", ""),
            "leading_change_pct": round(float(item.get("f136", 0) or 0), 2),
            "amount_yi": round(float(item.get("f20", 0) or 0) / 1e8, 2),
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
