import csv
import json
from pathlib import Path


def write_outputs(base_dir: Path, date_text: str, passed_rows: list[dict], all_rows: list[dict]) -> dict:
    output_dir = base_dir / 'outputs'
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f'auction_sniper_v2_{date_text}.csv'
    json_path = output_dir / f'auction_sniper_v2_{date_text}.json'
    md_path = output_dir / f'auction_sniper_v2_{date_text}.md'

    fields = [
        'mode', 'symbol', 'name', 'date', 'source', 'data_granularity',
        'price_092430', 'price_0915_ref', 'price_0919_high', 'price_0920_ref',
        'change_pct', 'volume_ratio', 'score', 'passed', 'fail_reasons', 'note',
    ]

    with csv_path.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in all_rows:
            writer.writerow({k: row.get(k) for k in fields})

    with json_path.open('w', encoding='utf-8') as f:
        json.dump({'passed': passed_rows, 'all': all_rows}, f, ensure_ascii=False, indent=2)

    md_lines = [f'# 集合竞价狙击手 V2 结果 {date_text}', '', f'入选数量：{len(passed_rows)}', '']
    for i, row in enumerate(passed_rows, 1):
        mode_zh = '三安模式' if row.get('mode') == 'sanan' else '金螳螂模式'
        md_lines.append(f"## {i}. [{mode_zh}] {row['name']}（{row['symbol'].upper()}）")
        md_lines.append(f"- 当前涨幅：{row['change_pct']}%")
        md_lines.append(f"- 竞价量比：{row['volume_ratio']}")
        md_lines.append(f"- 分数：{row['score']}")
        md_lines.append(f"- 来源：{row['source']} | 粒度：{row['data_granularity']}")
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
