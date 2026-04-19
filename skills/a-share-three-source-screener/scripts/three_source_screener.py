#!/usr/bin/env python3
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = BASE_DIR.parent.parent
HOT_SPOTS_DIR = WORKSPACE_DIR / "skills" / "a-share-hot-spots"
if str(HOT_SPOTS_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(HOT_SPOTS_DIR / "scripts"))

from market_watch import (  # type: ignore
    fetch_stock,
    fetch_index,
    fetch_hot_sectors,
    fetch_hot_stocks,
    fetch_industry_sectors,
    fetch_monthly_klines,
    resolve_names,
    safe_float,
)


INDEX_BENCHMARK_NAME = "上证指数"


def pick_market_benchmark(indexes: list[dict]) -> float:
    for item in indexes:
        if item.get("name") == INDEX_BENCHMARK_NAME:
            return safe_float(item.get("change_pct", 0))
    return safe_float(indexes[0].get("change_pct", 0)) if indexes else 0.0


def build_hot_maps(hot_stocks: list[dict], hot_sectors: list[dict], industry_sectors: list[dict]) -> tuple[dict, dict]:
    stock_hot = {}
    for rank, item in enumerate(hot_stocks, 1):
        symbol = str(item.get("symbol", "")).lower()
        code = symbol[2:] if len(symbol) > 2 else symbol
        stock_hot[code] = {
            "rank": rank,
            "name": item.get("name", ""),
            "change_pct": safe_float(item.get("change_pct", 0)),
            "amount_yi": safe_float(item.get("amount_yi", 0)),
        }

    sector_hot = {}
    for item in hot_sectors:
        leader = str(item.get("leading_stock", "")).strip()
        if leader:
            sector_hot[leader] = {
                "sector_type": "concept",
                "sector_name": item.get("name", ""),
                "sector_change_pct": safe_float(item.get("change_pct", 0)),
            }
    for item in industry_sectors:
        leader = str(item.get("leading_stock", "")).strip()
        if leader and leader not in sector_hot:
            sector_hot[leader] = {
                "sector_type": "industry",
                "sector_name": item.get("name", ""),
                "sector_change_pct": safe_float(item.get("change_pct", 0)),
            }
    return stock_hot, sector_hot


def analyze_history(code: str) -> dict:
    try:
        monthly = fetch_monthly_klines(code, 36)
    except Exception as e:
        return {"ok": False, "error": str(e)}

    if len(monthly) < 12:
        return {"ok": False, "error": "月线数据不足"}

    closes = [safe_float(x.get("close", 0)) for x in monthly]
    volumes = [safe_float(x.get("volume", 0)) for x in monthly]
    current_close = closes[-1]
    min_close = min(closes)
    max_close = max(closes)
    position = (current_close - min_close) / (max_close - min_close) if max_close > min_close else 0.0

    recent3_close = closes[-3:] if len(closes) >= 3 else closes
    recent3_vol = volumes[-3:] if len(volumes) >= 3 else volumes
    prev12 = volumes[-15:-3] if len(volumes) >= 15 else volumes[:-3]
    base_vol = sum(prev12) / len(prev12) if prev12 else 0.0
    rising = len(recent3_close) >= 3 and recent3_close[-1] > recent3_close[0]
    volume_expand = bool(base_vol and max(recent3_vol) > base_vol * 1.2)
    low_zone = position <= 0.55

    score = 0
    reasons = []
    if low_zone:
        score += 2
        reasons.append("月线位置仍不高")
    if rising:
        score += 2
        reasons.append("近3个月收盘抬升")
    if volume_expand:
        score += 2
        reasons.append("近月量能放大")

    return {
        "ok": True,
        "score": score,
        "position": round(position, 3),
        "recent3_close": [round(x, 2) for x in recent3_close],
        "recent3_volume": [round(x, 2) for x in recent3_vol],
        "base_volume": round(base_vol, 2),
        "reasons": reasons,
    }


def score_stock(stock: dict, benchmark_pct: float, hot_stock_map: dict, sector_hot_map: dict) -> dict:
    code = str(stock.get("code", ""))
    name = str(stock.get("name", "")).strip()
    change_pct = safe_float(stock.get("change_pct", 0))
    amount_yi = safe_float(stock.get("amount_yi", 0))

    realtime_score = 0
    realtime_reasons = []
    if change_pct >= 5:
        realtime_score += 3
        realtime_reasons.append("实时涨幅较强")
    elif change_pct >= 2:
        realtime_score += 2
        realtime_reasons.append("实时涨幅偏强")
    elif change_pct > 0:
        realtime_score += 1
        realtime_reasons.append("实时为红")

    if change_pct - benchmark_pct >= 2:
        realtime_score += 2
        realtime_reasons.append("明显强于大盘")
    elif change_pct > benchmark_pct:
        realtime_score += 1
        realtime_reasons.append("强于大盘")

    if amount_yi >= 20:
        realtime_score += 2
        realtime_reasons.append("成交额较大")
    elif amount_yi >= 8:
        realtime_score += 1
        realtime_reasons.append("有一定成交额")

    heat_score = 0
    heat_reasons = []
    hot_stock_info = hot_stock_map.get(code)
    if hot_stock_info:
        rank = int(hot_stock_info.get("rank", 99))
        if rank <= 5:
            heat_score += 3
            heat_reasons.append(f"进入热门股前{rank}")
        elif rank <= 10:
            heat_score += 2
            heat_reasons.append(f"进入热门股前{rank}")
        else:
            heat_score += 1
            heat_reasons.append("进入热门股名单")

    sector_info = sector_hot_map.get(name)
    if sector_info:
        heat_score += 2
        heat_reasons.append(f"属于热点{sector_info.get('sector_type')}龙头：{sector_info.get('sector_name')}")

    history = analyze_history(code)
    history_score = history.get("score", 0) if history.get("ok") else 0
    history_reasons = history.get("reasons", []) if history.get("ok") else [f"历史数据失败：{history.get('error', '未知错误')}"]

    total_score = realtime_score + heat_score + history_score
    tags = []
    if change_pct >= 5:
        tags.append("强势")
    if hot_stock_info:
        tags.append("热榜")
    if sector_info:
        tags.append("龙头")
    if history.get("ok") and history.get("position", 1) <= 0.55:
        tags.append("低位")
    if history.get("ok") and "近月量能放大" in history_reasons:
        tags.append("放量")

    return {
        "code": code,
        "symbol": stock.get("symbol", ""),
        "name": name,
        "current": safe_float(stock.get("current", 0)),
        "change_pct": round(change_pct, 2),
        "amount_yi": round(amount_yi, 2),
        "benchmark_pct": round(benchmark_pct, 2),
        "score": total_score,
        "scores": {
            "realtime": realtime_score,
            "heat": heat_score,
            "history": history_score,
        },
        "tags": tags,
        "hot_stock_rank": hot_stock_info.get("rank") if hot_stock_info else None,
        "sector_info": sector_info,
        "history": history,
        "reasons": realtime_reasons + heat_reasons + history_reasons,
    }


def build_candidate_pool() -> list[dict]:
    hot_stocks = fetch_hot_stocks()
    pool = []
    seen = set()
    for item in hot_stocks[:12]:
        code = str(item.get("symbol", "")).lower()[2:]
        if not code or code in seen:
            continue
        seen.add(code)
        detail = fetch_stock(code)
        if detail.get("error"):
            continue
        pool.append(detail)
    return pool


def run_scan(limit: int = 8, with_history: bool = True) -> dict:
    indexes = fetch_index()
    hot_sectors = fetch_hot_sectors()
    hot_stocks = fetch_hot_stocks()
    industry_sectors = fetch_industry_sectors()
    benchmark_pct = pick_market_benchmark(indexes)
    stock_hot_map, sector_hot_map = build_hot_maps(hot_stocks, hot_sectors, industry_sectors)
    pool = build_candidate_pool()
    scored = []
    for x in pool:
        if with_history:
            scored.append(score_stock(x, benchmark_pct, stock_hot_map, sector_hot_map))
        else:
            item = score_stock(x, benchmark_pct, stock_hot_map, sector_hot_map)
            item["score"] = item["scores"]["realtime"] + item["scores"]["heat"]
            item["scores"]["history"] = 0
            item["history"] = {"ok": False, "error": "轻量模式未拉月线"}
            item["reasons"] = [r for r in item.get("reasons", []) if not str(r).startswith("月线") and not str(r).startswith("近3个月") and not str(r).startswith("近月") and not str(r).startswith("历史数据失败")]
            scored.append(item)
    scored.sort(key=lambda x: (x.get("score", 0), x.get("change_pct", 0), x.get("amount_yi", 0)), reverse=True)
    return {
        "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "indexes": indexes,
        "benchmark_pct": benchmark_pct,
        "hot_sectors": hot_sectors[:5],
        "industry_sectors": industry_sectors[:5],
        "candidates": scored[:limit],
    }


def analyze_single_by_code(code: str) -> dict:
    indexes = fetch_index()
    hot_sectors = fetch_hot_sectors()
    hot_stocks = fetch_hot_stocks()
    industry_sectors = fetch_industry_sectors()
    benchmark_pct = pick_market_benchmark(indexes)
    stock_hot_map, sector_hot_map = build_hot_maps(hot_stocks, hot_sectors, industry_sectors)
    stock = fetch_stock(code)
    if stock.get("error"):
        return {"error": stock.get("error")}
    result = score_stock(stock, benchmark_pct, stock_hot_map, sector_hot_map)
    result["indexes"] = indexes
    return result


def fmt_candidate(item: dict, rank: int) -> str:
    tags = " / ".join(item.get("tags", [])) if item.get("tags") else "无"
    reasons = "；".join(item.get("reasons", [])[:4])
    return (
        f"{rank:02d}. {item['name']}（{str(item['symbol']).upper()}） 评分 {item['score']}\n"
        f"    现价 {item['current']} 元｜涨幅 {item['change_pct']}%｜成交额 {item['amount_yi']} 亿｜标签：{tags}\n"
        f"    说明：{reasons}"
    )


def fmt_scan(result: dict) -> str:
    candidates = result.get("candidates", [])
    indexes = result.get("indexes", [])
    lines = ["A股三源共振候选池"]
    if indexes:
        idx = indexes[0]
        lines.append(f"盘面基准：{idx['name']} {idx['current']:.2f}（{idx['change_pct']}%）")
    lines.append(f"更新时间：{result.get('fetch_time', '')}")
    lines.append("")
    if not candidates:
        lines.append("未筛到合适候选，可能是数据源异常或盘面过弱。")
        return "\n".join(lines)
    lines.append("优先盯盘名单：")
    for i, item in enumerate(candidates, 1):
        lines.append(fmt_candidate(item, i))
    return "\n".join(lines)


def fmt_brief(result: dict) -> str:
    candidates = result.get("candidates", [])[:3]
    if not candidates:
        return "三源短评：暂未筛到明显候选"
    parts = ["三源短评："]
    for item in candidates:
        parts.append(f"{item['name']}({item['score']}分,{item['change_pct']}%)")
    return "｜".join(parts)


def fmt_single(item: dict) -> str:
    if item.get("error"):
        return f"失败：{item['error']}"
    tags = " / ".join(item.get("tags", [])) if item.get("tags") else "无"
    lines = [
        f"三源评分：{item['name']}（{str(item['symbol']).upper()}）",
        f"总分：{item['score']}｜实时 {item['scores']['realtime']} / 热度 {item['scores']['heat']} / 历史 {item['scores']['history']}",
        f"现价：{item['current']} 元｜涨幅：{item['change_pct']}%｜成交额：{item['amount_yi']} 亿",
        f"标签：{tags}",
    ]
    if item.get("sector_info"):
        sec = item["sector_info"]
        lines.append(f"热点归属：{sec.get('sector_name')}（{sec.get('sector_type')}）")
    history = item.get("history", {})
    if history.get("ok"):
        lines.append(
            f"月线位置：{history.get('position')}｜近3月收盘：{history.get('recent3_close')}｜近3月量能：{history.get('recent3_volume')}"
        )
    lines.append("说明：")
    for reason in item.get("reasons", []):
        lines.append(f"- {reason}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="A股三源共振筛股")
    parser.add_argument("--scan", action="store_true", help="扫描候选池")
    parser.add_argument("--brief", action="store_true", help="输出短摘要")
    parser.add_argument("--pool", action="store_true", help="仅看热榜候选池")
    parser.add_argument("--code", help="按代码查单股")
    parser.add_argument("--name", help="按中文名查单股")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    if args.scan:
        result = run_scan(limit=8, with_history=True)
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else fmt_scan(result))
        return

    if args.brief:
        result = run_scan(limit=3, with_history=False)
        print(json.dumps(result.get("candidates", [])[:3], ensure_ascii=False, indent=2) if args.json else fmt_brief(result))
        return

    if args.pool:
        pool = build_candidate_pool()
        print(json.dumps(pool, ensure_ascii=False, indent=2) if args.json else "\n".join([f"{x['name']} {x['change_pct']}% {x['amount_yi']}亿" for x in pool]))
        return

    if args.name:
        resolved = resolve_names([args.name])
        result = analyze_single_by_code(resolved[0])
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else fmt_single(result))
        return

    if args.code:
        result = analyze_single_by_code(args.code)
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else fmt_single(result))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
