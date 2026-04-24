from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable

DEFAULT_UNIVERSE_PATH = Path(__file__).resolve().parents[1] / 'auction_915_925_smooth_scanner' / 'outputs' / 'sz_mainboard_00_universe.json'


@dataclass
class UniverseFilters:
    allow_markets: tuple[str, ...] = ('sz',)
    include_prefixes: tuple[str, ...] = ('00',)
    exclude_prefixes: tuple[str, ...] = ('300', '301', '688', '689', '8', '4')
    exclude_st: bool = True
    exclude_delisting: bool = True
    min_listed_days: int = 60
    max_float_mkt_cap: float | None = None
    max_liutongguben: float | None = None
    limit: int | None = None


@dataclass
class UniverseRow:
    code: str
    name: str
    market: str
    days_since_list: int | None = None
    security_type: str | None = 'stock'
    float_mkt_cap: float | None = None
    liutongguben: float | None = None
    reasons: list[str] | None = None


def _normalize_market_code(code: str) -> tuple[str, str]:
    raw = str(code or '').strip().lower()
    if raw.startswith(('sh', 'sz')):
        market = raw[:2]
        digits = ''.join(ch for ch in raw[2:] if ch.isdigit())
        return market, digits
    digits = ''.join(ch for ch in raw if ch.isdigit())
    market = 'sh' if digits.startswith(('60', '68', '51', '58', '11')) else 'sz'
    return market, digits


def _passes_filters(row: dict, filters: UniverseFilters) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    market, digits = _normalize_market_code(row.get('code', ''))
    name = str(row.get('name') or digits)
    upper_name = name.upper()
    days_since_list = row.get('days_since_list')
    security_type = str(row.get('security_type') or 'stock').lower()
    float_mkt_cap = row.get('float_mkt_cap')
    liutongguben = row.get('liutongguben')

    if filters.allow_markets and market not in filters.allow_markets:
        reasons.append('market_filtered')
    if filters.include_prefixes and not digits.startswith(filters.include_prefixes):
        reasons.append('prefix_not_included')
    if filters.exclude_prefixes and digits.startswith(filters.exclude_prefixes):
        reasons.append('prefix_excluded')
    if security_type not in {'stock', '', 'common_stock'}:
        reasons.append('non_stock_security_type')
    if filters.exclude_st and 'ST' in upper_name:
        reasons.append('st_flag')
    if filters.exclude_delisting and ('退' in name or upper_name.startswith(('N', 'C'))):
        reasons.append('delisting_or_new_name_flag')
    if filters.min_listed_days and isinstance(days_since_list, (int, float)) and days_since_list < filters.min_listed_days:
        reasons.append('listed_lt_min_days')
    if filters.max_float_mkt_cap is not None and isinstance(float_mkt_cap, (int, float)) and float_mkt_cap > filters.max_float_mkt_cap:
        reasons.append('float_mkt_cap_gt_limit')
    if filters.max_liutongguben is not None and isinstance(liutongguben, (int, float)) and liutongguben > filters.max_liutongguben:
        reasons.append('liutongguben_gt_limit')
    return (len(reasons) == 0, reasons)


def load_shared_universe(universe_path: str | Path | None = None, filters: UniverseFilters | None = None) -> dict:
    path = Path(universe_path) if universe_path else DEFAULT_UNIVERSE_PATH
    if not path.exists():
        return {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source_path': str(path),
            'selected_count': 0,
            'excluded_count': 0,
            'selected': [],
            'excluded': [],
        }

    obj = json.loads(path.read_text(encoding='utf-8'))
    raw_selected = obj.get('selected') or []
    use_filters = filters or UniverseFilters()
    selected: list[dict] = []
    excluded: list[dict] = []

    for raw in raw_selected:
        market, digits = _normalize_market_code(raw.get('code', ''))
        row = {
            'code': digits,
            'name': str(raw.get('name') or digits),
            'market': market,
            'days_since_list': raw.get('days_since_list'),
            'security_type': raw.get('security_type') or 'stock',
            'float_mkt_cap': raw.get('float_mkt_cap'),
            'liutongguben': raw.get('liutongguben'),
            'reasons': list(raw.get('reasons') or []),
        }
        ok, filter_reasons = _passes_filters(row, use_filters)
        row['reasons'] = list(dict.fromkeys((row.get('reasons') or []) + filter_reasons))
        if ok:
            selected.append(row)
        else:
            excluded.append(row)

    if use_filters.limit:
        selected = selected[: use_filters.limit]

    return {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'source_path': str(path),
        'filters': asdict(use_filters),
        'selected_count': len(selected),
        'excluded_count': len(excluded),
        'selected': selected,
        'excluded': excluded,
    }


def codes_from_universe(universe: dict) -> list[str]:
    out = []
    for row in universe.get('selected', []):
        market = str(row.get('market') or 'sz').lower()
        code = str(row.get('code') or '').strip()
        if not code:
            continue
        out.append(f'{market}{code}')
    return out


def names_from_universe(universe: dict) -> dict[str, str]:
    mapping = {}
    for row in universe.get('selected', []):
        code = str(row.get('code') or '').strip()
        if not code:
            continue
        mapping[code] = str(row.get('name') or code)
    return mapping
