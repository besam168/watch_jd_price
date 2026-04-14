#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CALIBRATION_PATH = ROOT / "calibration.json"


def load_calibration() -> dict:
    if not CALIBRATION_PATH.exists():
        raise FileNotFoundError(f"Calibration file not found: {CALIBRATION_PATH}")
    return json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))


def save_calibration(data: dict) -> None:
    CALIBRATION_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_show(_: argparse.Namespace) -> int:
    data = load_calibration()
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def cmd_convert(args: argparse.Namespace) -> int:
    data = load_calibration()
    model = data.get("model", {})
    x_model = model.get("x", {"a": 1.0, "b": 0.0})
    y_model = model.get("y", {"a": 1.0, "b": 0.0})

    x_real = x_model.get("a", 1.0) * args.x + x_model.get("b", 0.0)
    y_real = y_model.get("a", 1.0) * args.y + y_model.get("b", 0.0)

    result = {
        "input": {"x": args.x, "y": args.y},
        "output": {"x": round(x_real, 2), "y": round(y_real, 2)},
        "screen": data.get("screen", {}),
        "model": model,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_add_sample(args: argparse.Namespace) -> int:
    data = load_calibration()
    samples = data.setdefault("samples", [])
    sample = {
        "label": args.label,
        "source": args.source,
        "real": {"x": args.real_x, "y": args.real_y},
        "ocr": None if args.ocr_x is None or args.ocr_y is None else {"x": args.ocr_x, "y": args.ocr_y},
        "comment": args.comment or "",
    }
    samples.append(sample)
    save_calibration(data)
    print(json.dumps({"ok": True, "added": sample, "count": len(samples)}, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Desktop coordinate calibration helper V1")
    sub = parser.add_subparsers(dest="cmd", required=True)

    show_p = sub.add_parser("show")
    show_p.set_defaults(func=cmd_show)

    convert_p = sub.add_parser("convert")
    convert_p.add_argument("x", type=float)
    convert_p.add_argument("y", type=float)
    convert_p.set_defaults(func=cmd_convert)

    add_p = sub.add_parser("add-sample")
    add_p.add_argument("label")
    add_p.add_argument("real_x", type=float)
    add_p.add_argument("real_y", type=float)
    add_p.add_argument("--ocr-x", type=float)
    add_p.add_argument("--ocr-y", type=float)
    add_p.add_argument("--source", default="manual")
    add_p.add_argument("--comment", default="")
    add_p.set_defaults(func=cmd_add_sample)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
