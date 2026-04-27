import csv
import json
from pathlib import Path


def mode_label(mode: str) -> str:
    if mode == 'sanan':
        return '三安模式'
    if mode == 'jinmantang':
        return '金螳螂模式'
    return '未入选'


def compact_line(row: dict) -> str:
    return f"[{mode_label(row.get('mode', ''))}] {row.get('symbol', '').upper()} - {row.get('name', '')} - {row.get('change_pct')}% - 量比{row.get('volume_ratio')}"


def write_outputs(base_dir: Path, date_text: str, passed_rows: list[dict], all_rows: list[dict]) -> dict:
    output_dir = base_dir / 'outputs'
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f'auction_sniper_v2_{date_text}.csv'
    json_path = output_dir / f'auction_sniper_v2_{date_text}.json'
    md_path = output_dir / f'auction_sniper_v2_{date_text}.md'

    fields = [
        'mode', 'symbol', 'name', 'date', 'source', 'data_granularity',
        'price_092430', 'price_0915_ref', 'price_0919_high', 'price_0920_ref',
        'change_pct', 'volume_ratio', 'passed', 'fail_reasons', 'note', 'compact_line',
    ]

    with csv_path.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in all_rows:
            row2 = dict(row)
            row2['compact_line'] = compact_line(row2) if row2.get('passed') else ''
            writer.writerow({k: row2.get(k) for k in fields})

    json_payload = {
        'passed': [dict(x, compact_line=compact_line(x)) for x in passed_rows],
        'all': all_rows,
    }
    with json_path.open('w', encoding='utf-8') as f:
        json.dump(json_payload, f, ensure_ascii=False, indent=2)

    md_lines = [f'# 集合竞价狙击手 V2 结果 {date_text}', '', f'入选数量：{len(passed_rows)}', '']
    for i, row in enumerate(passed_rows, 1):
        md_lines.append(f"## {i}. {compact_line(row)}")
        note = row.get('note')
        if note:
            md_lines.append(f"- 说明：{note}")
        md_lines.append('')

    md_path.write_text('\n'.join(md_lines), encoding='utf-8')
    return {
        'csv': str(csv_path),
        'json': str(json_path),
        'md': str(md_path),
    }
