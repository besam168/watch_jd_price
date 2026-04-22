#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

MANUAL_SECTOR_MAP = {
    '603318': ['燃气', '公用事业'],
    '600234': ['地产链', '区域开发'],
    '002360': ['化工', '民爆'],
    '605588': ['消费电子', '显示材料'],
    '603496': ['算力', 'AI硬件'],
    '603903': ['环保', '公用事业'],
    '002730': ['消费电子', '智能设备'],
    '605077': ['食品', '代糖'],
    '603217': ['化工', '新材料'],
    '002955': ['教育设备', 'AI教育'],
    '603178': ['汽车零部件', '机器人'],
    '605100': ['柴油机', '机械设备'],
    '000722': ['电力', '绿色能源'],
    '603586': ['汽车零部件'],
    '000159': ['贸易', '油气'],
    '603139': ['医药', '中药'],
    '002391': ['农药化工'],
    '002842': ['小金属', '新材料'],
    '000526': ['教育', '职业培训'],
    '000890': ['金属包装', '新材料'],
    '002866': ['消费电子', '固态电池'],
    '003023': ['家电', '消费'],
    '600191': ['农产品', '消费'],
    '603130': ['纺织服装'],
    '002667': ['工程机械', '专用设备'],
    '002845': ['消费电子', '面板链'],
    '002674': ['消费电子', '智能终端'],
    '600367': ['小金属', '资源品'],
    '600678': ['水泥建材', '基建'],
    '002970': ['安防', '人工智能'],
    '603788': ['汽车零部件'],
    '603637': ['环保', '公用事业'],
    '002635': ['消费电子', '精密制造'],
    '600156': ['纺织服装', '国企改革'],
    '000551': ['环保设备', '创投'],
    '002887': ['机械设备', '高端装备'],
    '003027': ['消费电子', '面板链'],
    '002935': ['军工电子'],
    '603926': ['汽车零部件'],
    '603038': ['汽车零部件'],
    '603266': ['汽车零部件'],
    '601007': ['酒店旅游', '消费'],
    '002846': ['金属包装', '消费包装'],
    '600969': ['电力'],
    '603991': ['化工', '新材料'],
    '002395': ['化工', '新材料'],
    '603587': ['汽车零部件'],
    '603331': ['消费电子', 'AI硬件'],
    '603667': ['消费电子', '精密制造'],
    '603887': ['消费电子', 'AI硬件'],
    '603327': ['医药', '创新药'],
    '600589': ['有色金属', '资源品'],
    '600281': ['电力设备', '绿色能源'],
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def get_pool(data: dict):
    merged = {}
    for key in ['true_leaders', 'strong_followers', 'watchlist']:
        for item in data.get(key, []) or []:
            code = str(item.get('code') or '').strip()
            if code and code not in merged:
                merged[code] = item
    return list(merged.values())


def classify(code: str):
    return MANUAL_SECTOR_MAP.get(code, ['未分类'])


def summarize(items: list[dict]):
    counter = Counter()
    grouped = defaultdict(list)
    for item in items:
        code = str(item.get('code') or '')
        name = item.get('name') or code
        tags = classify(code)
        item['sector_tags'] = tags
        item['primary_sector'] = tags[0]
        for sec in tags[:2]:
            counter[sec] += 1
            grouped[sec].append(item)

    out = []
    for sec, cnt in counter.most_common():
        sector_items = grouped[sec]
        sector_items_sorted = sorted(
            sector_items,
            key=lambda x: (float(x.get('change_pct', 0) or 0), float(x.get('track_score', 0) or 0), float(x.get('intraday_score', 0) or 0)),
            reverse=True,
        )
        leader = sector_items_sorted[0] if sector_items_sorted else None
        followers = sector_items_sorted[1:4] if len(sector_items_sorted) > 1 else []
        out.append({
            'sector': sec,
            'count': cnt,
            'leader': {
                'name': leader.get('name'),
                'code': leader.get('code'),
                'change_pct': leader.get('change_pct'),
            } if leader else None,
            'followers': [
                {
                    'name': x.get('name'),
                    'code': x.get('code'),
                    'change_pct': x.get('change_pct'),
                }
                for x in followers
            ],
            'examples': [f"{x.get('name')} {x.get('code')}" for x in sector_items_sorted[:3]],
        })
    return out, items


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--slot', default='live')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    data = load_json(Path(args.input))
    pool = get_pool(data)
    hot_sectors, enriched = summarize(pool)
    payload = {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'slot': args.slot,
        'pool_size': len(pool),
        'hot_sectors': hot_sectors,
        'items': enriched,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
