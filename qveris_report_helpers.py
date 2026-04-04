from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent

TOOL_NEWS = "newsdata.news.search.v1.b65ccc56"
TOOL_STOCK = "finnhub_io_api.stock.quote"
TOOL_COMMODITY = "financialmodelingprep.stable.quote.retrieve.v1.822497ca"


def _run_qveris(tool_id: str, params: dict[str, Any], timeout: int = 45) -> dict[str, Any] | None:
    script = (
        "import json; from openclaw.extensions.qveris import api; "
        f"print(json.dumps(api.call_tool('{tool_id}', {json.dumps(params, ensure_ascii=False)}), ensure_ascii=False))"
    )
    try:
        completed = subprocess.run(
            ["python", "-c", script],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except Exception:
        return None

    if completed.returncode != 0:
        return None

    stdout = (completed.stdout or "").strip()
    if not stdout:
        return None

    try:
        return json.loads(stdout)
    except Exception:
        return None


def fetch_news_items() -> list[dict[str, str]]:
    params = {
        "q": "global markets OR geopolitics OR US China OR Russia Ukraine OR Middle East OR AI OR robotics",
        "language": "en",
        "timeframe": "24",
        "size": 8,
        "removeduplicate": "1",
        "sort": "date",
    }
    data = _run_qveris(TOOL_NEWS, params)
    if not isinstance(data, dict):
        return []

    raw_items = data.get("results") or data.get("articles") or data.get("data") or []
    items: list[dict[str, str]] = []
    if not isinstance(raw_items, list):
        return []

    for item in raw_items[:8]:
        if not isinstance(item, dict):
            continue
        items.append(
            {
                "source": str(item.get("source_id") or item.get("source_name") or item.get("source") or "QVeris"),
                "title": str(item.get("title") or "").strip(),
                "link": str(item.get("link") or item.get("url") or "").strip(),
                "pub_date": str(item.get("pubDate") or item.get("publishedAt") or item.get("pub_date") or "").strip(),
                "summary": str(item.get("description") or item.get("content") or item.get("snippet") or "").strip(),
            }
        )
    return [x for x in items if x.get("title")]


def fetch_stock_quote(symbol: str) -> dict[str, Any] | None:
    data = _run_qveris(TOOL_STOCK, {"symbol": symbol})
    return data if isinstance(data, dict) else None


def fetch_commodity_quote(symbol: str) -> dict[str, Any] | None:
    data = _run_qveris(TOOL_COMMODITY, {"symbol": symbol})
    return data if isinstance(data, dict) else None
