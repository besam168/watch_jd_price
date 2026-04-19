import csv
import json
from dataclasses import asdict
from pathlib import Path


def write_outputs(base_dir: Path, date_text: str, passed_rows: list[dict], all_rows: list[dict]) -> dict:
    output_dir = base_dir / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"auction_smooth_{date_text}.csv"
    json_path = output_dir / f"auction_smooth_{date_text}.json"
    md_path = output_dir / f"auction_smooth_{date_text}.md"

    fields = [
        "symbol", "name", "date", "source", "data_granularity", "tick_count",
        "auction_open_price", "auction_last_price", "auction_high", "auction_low",
        "range_ratio", "jump_std_ratio", "change_ratio", "rmse_ratio",
        "auction_amt", "amt_float_ratio", "smooth_score", "passed", "fail_reasons",
    ]

    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in all_rows:
            writer.writerow({k: row.get(k) for k in fields})

    with json_path.open("w", encoding="utf-8") as f:
        json.dump({"passed": passed_rows, "all": all_rows}, f, ensure_ascii=False, indent=2)

    md_lines = [f"# 竞价平滑扫描结果 {date_text}", "", f"入选数量：{len(passed_rows)}", ""]
    for i, row in enumerate(passed_rows, 1):
        md_lines.append(f"## {i}. {row['name']}（{row['symbol'].upper()}）")
        md_lines.append(f"- 分数：{row['smooth_score']}")
        md_lines.append(f"- 来源：{row['source']} | 粒度：{row['data_granularity']}")
        md_lines.append(f"- 指标：range={row['range_ratio']} jump_std={row['jump_std_ratio']} change={row['change_ratio']} rmse={row['rmse_ratio']} liq={row['amt_float_ratio']}")
        md_lines.append("")

    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    return {
        "csv": str(csv_path),
        "json": str(json_path),
        "md": str(md_path),
    }
