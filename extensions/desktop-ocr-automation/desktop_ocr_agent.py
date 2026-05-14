import argparse
import ctypes
import json
import logging
import os
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pyautogui
from PIL import Image, ImageDraw, ImageGrab

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
SCREENSHOT_DIR = BASE_DIR / "screenshots"
LOG_DIR = BASE_DIR / "logs"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOG_DIR / "run.log"


@dataclass
class OcrItem:
    text: str
    confidence: float
    box: List[Tuple[float, float]]
    center: Tuple[int, int]


def setup_stdio() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"缺少配置文件: {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def get_primary_screen_bbox() -> Tuple[int, int, int, int]:
    """Return Windows primary monitor bbox in virtual-screen coordinates."""
    user32 = ctypes.windll.user32
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass
    width = int(user32.GetSystemMetrics(0))
    height = int(user32.GetSystemMetrics(1))
    return (0, 0, width, height)


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def capture_primary_screen() -> Tuple[Image.Image, Path, Tuple[int, int, int, int]]:
    bbox = get_primary_screen_bbox()
    img = ImageGrab.grab(bbox=bbox, all_screens=True)
    path = SCREENSHOT_DIR / f"primary_{timestamp()}.png"
    img.save(path)
    latest = SCREENSHOT_DIR / "latest_primary.png"
    img.save(latest)
    logging.info("已截取主屏幕: bbox=%s path=%s", bbox, path)
    return img, path, bbox


def get_paddle_ocr(config: Dict[str, Any]):
    try:
        from paddleocr import PaddleOCR
    except Exception as e:
        raise RuntimeError(
            "未安装 PaddleOCR。请先运行 install_deps.bat，或执行: "
            "python -m pip install paddleocr pyautogui pillow opencv-python numpy"
        ) from e
    ocr_cfg = config.get("ocr", {})
    lang = ocr_cfg.get("lang", "ch")
    use_angle_cls = bool(ocr_cfg.get("use_angle_cls", True))
    base_kwargs = {
        "lang": lang,
        "use_doc_orientation_classify": False,
        "use_doc_unwarping": False,
        "use_textline_orientation": use_angle_cls,
    }
    for kwargs in (
        base_kwargs,
        {**base_kwargs, "show_log": False},
        {"use_textline_orientation": use_angle_cls, "lang": lang},
        {"use_angle_cls": use_angle_cls, "lang": lang},
        {"lang": lang},
    ):
        try:
            return PaddleOCR(**kwargs)
        except (TypeError, ValueError) as e:
            logging.info("PaddleOCR 参数不兼容，尝试下一组参数: %s error=%s", kwargs, e)
    raise RuntimeError("无法初始化 PaddleOCR，请检查 paddleocr/paddlepaddle 版本。")


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "").lower()


def _as_result_dict(page: Any) -> Optional[Dict[str, Any]]:
    if isinstance(page, dict):
        return page.get("res", page) if isinstance(page.get("res", page), dict) else page
    data = getattr(page, "json", None)
    if isinstance(data, dict):
        res = data.get("res", data)
        return res if isinstance(res, dict) else data
    data = getattr(page, "res", None)
    if isinstance(data, dict):
        return data
    return None


def _coerce_box(box: Any) -> List[Tuple[float, float]]:
    return [(float(p[0]), float(p[1])) for p in box]


def _append_item(items: List[OcrItem], text: Any, conf: Any, box: Any, min_conf: float) -> None:
    try:
        text_value = str(text)
        conf_value = float(conf)
        box_value = _coerce_box(box)
    except Exception:
        return
    if not text_value or conf_value < min_conf or not box_value:
        return
    xs = [p[0] for p in box_value]
    ys = [p[1] for p in box_value]
    center = (int(sum(xs) / len(xs)), int(sum(ys) / len(ys)))
    items.append(OcrItem(text=text_value, confidence=conf_value, box=box_value, center=center))


def parse_ocr_result(raw: Any, min_conf: float) -> List[OcrItem]:
    items: List[OcrItem] = []
    if not raw:
        return items
    pages = raw if isinstance(raw, list) else [raw]
    for page in pages:
        if not page:
            continue
        result = _as_result_dict(page)
        if result:
            texts = result.get("rec_texts") or []
            scores = result.get("rec_scores") or []
            boxes = result.get("rec_polys") or result.get("dt_polys") or result.get("rec_boxes") or []
            for text, score, box in zip(texts, scores, boxes):
                first = box[0] if box is not None and len(box) > 0 else None
                if first is not None and isinstance(first, (int, float)) and len(box) == 4:
                    left, top, right, bottom = [float(v) for v in box]
                    box = [(left, top), (right, top), (right, bottom), (left, bottom)]
                _append_item(items, text, score, box, min_conf)
            continue

        # PaddleOCR classic output: [[box, (text, conf)], ...]
        lines = page if isinstance(page, list) else []
        for line in lines:
            try:
                box = line[0]
                text = line[1][0]
                conf = line[1][1]
            except Exception:
                continue
            _append_item(items, text, conf, box, min_conf)
    return items


def run_ocr(image_path: Path, config: Dict[str, Any]) -> List[OcrItem]:
    ocr = get_paddle_ocr(config)
    try:
        raw = ocr.ocr(str(image_path), cls=bool(config.get("ocr", {}).get("use_angle_cls", True)))
    except TypeError as e:
        logging.info("PaddleOCR ocr(cls=...) 不兼容，改用 predict(): %s", e)
        if hasattr(ocr, "predict"):
            raw = ocr.predict(str(image_path))
        else:
            raw = ocr.ocr(str(image_path))
    min_conf = float(config.get("ocr", {}).get("confidence_min", 0.55))
    items = parse_ocr_result(raw, min_conf)
    logging.info("OCR 完成: %s 个结果", len(items))
    for item in items:
        logging.info("OCR: text=%r conf=%.3f center=%s", item.text, item.confidence, item.center)
    return items


def save_debug_overlay(img: Image.Image, items: List[OcrItem], target: str = "") -> Path:
    debug = img.copy()
    draw = ImageDraw.Draw(debug)
    for item in items:
        pts = item.box
        flat = [(int(x), int(y)) for x, y in pts]
        color = "red" if target and normalize_text(target) in normalize_text(item.text) else "lime"
        draw.line(flat + [flat[0]], fill=color, width=3)
        draw.text(item.center, f"{item.text} {item.confidence:.2f}", fill=color)
    path = SCREENSHOT_DIR / f"debug_{timestamp()}.png"
    debug.save(path)
    latest = SCREENSHOT_DIR / "latest_debug.png"
    debug.save(latest)
    logging.info("已保存 debug 标注图: %s", path)
    return path


def match_item(items: List[OcrItem], target: str, match_mode: str = "contains") -> Optional[OcrItem]:
    target_norm = normalize_text(target)
    if not target_norm:
        return None
    matches: List[OcrItem] = []
    for item in items:
        text_norm = normalize_text(item.text)
        if match_mode == "exact":
            ok = text_norm == target_norm
        elif match_mode == "regex":
            ok = re.search(target, item.text) is not None
        else:
            ok = target_norm in text_norm
        if ok:
            matches.append(item)
    if not matches:
        return None
    matches.sort(key=lambda x: x.confidence, reverse=True)
    return matches[0]


def click_item(item: OcrItem, bbox: Tuple[int, int, int, int], config: Dict[str, Any], dry_run: bool = False) -> Tuple[int, int]:
    left, top, _, _ = bbox
    x = left + item.center[0]
    y = top + item.center[1]
    if dry_run:
        logging.info("dry-run: 将点击 %r center=(%s,%s) screen=(%s,%s)", item.text, item.center[0], item.center[1], x, y)
        return x, y
    pyautogui.moveTo(x, y, duration=float(config.get("click", {}).get("move_duration", 0.15)))
    pyautogui.click(x, y)
    time.sleep(float(config.get("click", {}).get("after_click_sleep", 0.5)))
    logging.info("已点击 %r screen=(%s,%s)", item.text, x, y)
    return x, y


def choose_item(items: List[OcrItem], target: str, match_mode: str = "contains") -> Tuple[Optional[OcrItem], List[OcrItem]]:
    target_norm = normalize_text(target)
    if not target_norm:
        return None, []
    matches: List[OcrItem] = []
    for item in items:
        text_norm = normalize_text(item.text)
        if match_mode == "exact":
            ok = text_norm == target_norm
        elif match_mode == "regex":
            ok = re.search(target, item.text) is not None
        else:
            ok = target_norm in text_norm
        if ok:
            matches.append(item)
    if not matches:
        return None, []
    matches.sort(key=lambda x: x.confidence, reverse=True)
    return matches[0], matches


def dump_results(items: List[OcrItem]) -> Path:
    path = LOG_DIR / f"ocr_results_{timestamp()}.json"
    path.write_text(json.dumps([asdict(x) for x in items], ensure_ascii=False, indent=2), encoding="utf-8")
    latest = LOG_DIR / "latest_ocr_results.json"
    latest.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    cfg = load_config() if CONFIG_PATH.exists() else {}
    default_task = cfg.get("default_task", {})
    parser = argparse.ArgumentParser(description="主屏幕中文 OCR 点击工具")
    parser.add_argument("--text", default=default_task.get("target_text", ""), help="要点击的文字，例如：确定")
    parser.add_argument("--match", choices=["contains", "exact", "regex"], default=default_task.get("match_mode", "contains"), help="文字匹配方式")
    parser.add_argument("--scan", action="store_true", help="只截图并 OCR，不点击")
    parser.add_argument("--dry-run", action="store_true", default=bool(default_task.get("dry_run", False)), help="只显示将点击的位置，不真实点击")
    parser.add_argument("--click", action="store_true", help="强制真实点击；会覆盖配置里的 dry_run=true")
    parser.add_argument("--fail-if-multiple", action="store_true", help="若匹配到多个候选则直接失败，避免误点")
    parser.add_argument("--list-matches", action="store_true", help="输出所有匹配候选，便于人工确认")
    return parser.parse_args()


def main() -> int:
    setup_stdio()
    setup_logging()
    args = parse_args()
    config = load_config()
    if args.click:
        args.dry_run = False

    logging.info("启动主屏 OCR 自动化：text=%r match=%s scan=%s dry_run=%s", args.text, args.match, args.scan, args.dry_run)
    img, image_path, bbox = capture_primary_screen()
    items = run_ocr(image_path, config)
    dump_path = dump_results(items)
    save_debug_overlay(img, items, args.text)
    print(f"OCR 结果已保存: {dump_path}")
    print(f"主屏截图: {image_path}")

    if args.scan:
        print("只扫描不点击。识别到的文字：")
        for item in items:
            print(f"- {item.text} conf={item.confidence:.3f} center={item.center}")
        return 0

    if not args.text:
        print("未提供 --text，无法点击。")
        return 2

    item, matches = choose_item(items, args.text, args.match)
    if item is None:
        print(f"未找到目标文字: {args.text}")
        logging.warning("未找到目标文字: %r", args.text)
        return 1

    if args.list_matches:
        print(f"匹配候选数量: {len(matches)}")
        for idx, candidate in enumerate(matches, start=1):
            print(
                f"[{idx}] text={candidate.text!r} conf={candidate.confidence:.3f} center={candidate.center}"
            )

    if args.fail_if_multiple and len(matches) > 1:
        print(f"匹配到多个候选({len(matches)})，已按安全策略停止，不执行点击。")
        logging.warning("匹配到多个候选，按安全策略停止: count=%s target=%r", len(matches), args.text)
        return 3

    x, y = click_item(item, bbox, config, dry_run=args.dry_run)
    action = "将点击(dry-run)" if args.dry_run else "已点击"
    print(f"{action}: text={item.text!r} conf={item.confidence:.3f} screen=({x},{y})")
    if args.dry_run:
        print("当前是 dry-run，没有真实点击。确认无误后可加 --click 执行真实点击。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
