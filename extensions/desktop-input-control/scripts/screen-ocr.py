import argparse
import json
import os
import re
import sys
import traceback
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageEnhance, ImageOps
import pytesseract
from pytesseract import Output

DEFAULT_LANG = "chi_sim+eng"
PREPROCESS_MODES = {
    "raw",
    "gray",
    "binary",
    "upscale2x",
    "gray_upscale2x",
    "high_contrast",
}
QUERY_MODES = {"contains", "exact"}
GROUP_BY_MODES = {"word", "line", "phrase", "auto"}
DEFAULT_TOP_N = 1


class OcrEngineError(RuntimeError):
    pass


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = re.sub(r"\s+", " ", value).strip()
    return value.lower()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OCR on an image and emit JSON.")
    parser.add_argument("image_path")
    parser.add_argument("lang", nargs="?", default=DEFAULT_LANG)
    parser.add_argument("--preprocess", choices=sorted(PREPROCESS_MODES), default="gray_upscale2x")
    parser.add_argument("--x", type=int)
    parser.add_argument("--y", type=int)
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--query")
    parser.add_argument("--query-mode", choices=sorted(QUERY_MODES), default="contains")
    parser.add_argument("--group-by", choices=sorted(GROUP_BY_MODES), default="auto")
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--debug-overlay")
    parser.add_argument("--engine", choices=["auto", "rapidocr", "tesseract"], default="auto")
    parser.add_argument("--psm", default="auto")
    return parser.parse_args()


def apply_preprocess(image: Image.Image, mode: str) -> Image.Image:
    if mode == "raw":
        return image.copy()

    if mode == "gray":
        return ImageOps.grayscale(image)

    if mode == "binary":
        gray = ImageOps.grayscale(image)
        return gray.point(lambda p: 255 if p >= 160 else 0)

    if mode == "upscale2x":
        width, height = image.size
        return image.resize((max(1, width * 2), max(1, height * 2)), Image.Resampling.LANCZOS)

    if mode == "gray_upscale2x":
        gray = ImageOps.grayscale(image)
        width, height = gray.size
        return gray.resize((max(1, width * 2), max(1, height * 2)), Image.Resampling.LANCZOS)

    if mode == "high_contrast":
        gray = ImageOps.grayscale(image)
        contrasted = ImageEnhance.Contrast(gray).enhance(2.5)
        sharpened = ImageEnhance.Sharpness(contrasted).enhance(1.8)
        return sharpened.point(lambda p: 255 if p >= 145 else 0)

    return image.copy()


def clamp_roi(image: Image.Image, x, y, width, height):
    if x is None and y is None and width is None and height is None:
        return image, {"x": 0, "y": 0, "width": image.width, "height": image.height, "applied": False}

    roi_x = max(0, int(x or 0))
    roi_y = max(0, int(y or 0))
    max_width = max(0, image.width - roi_x)
    max_height = max(0, image.height - roi_y)
    roi_width = max(0, int(width if width is not None else max_width))
    roi_height = max(0, int(height if height is not None else max_height))
    roi_width = min(roi_width, max_width)
    roi_height = min(roi_height, max_height)

    if roi_width <= 0 or roi_height <= 0:
        raise ValueError("invalid ROI after clamping")

    cropped = image.crop((roi_x, roi_y, roi_x + roi_width, roi_y + roi_height))
    return cropped, {"x": roi_x, "y": roi_y, "width": roi_width, "height": roi_height, "applied": True}


def item_matches(normalized_text_value: str, normalized_query: str, query_mode: str) -> bool:
    if not normalized_query:
        return True
    if query_mode == "exact":
        return normalized_text_value == normalized_query
    return normalized_query in normalized_text_value


def safe_float(value: Any, default: float = -1.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


WORD_KEYS = (
    "text",
    "normalizedText",
    "confidence",
    "x",
    "y",
    "w",
    "h",
    "centerX",
    "centerY",
    "lineNum",
    "blockNum",
    "parNum",
    "source",
)


def build_word_items_from_tesseract(data: Dict[str, List[Any]], roi: Dict[str, Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    item_count = len(data.get("text", []))
    for i in range(item_count):
        text = (data["text"][i] or "").strip()
        if not text:
            continue

        conf = safe_float(data["conf"][i])
        if conf < 0:
            continue

        left = int(data["left"][i])
        top = int(data["top"][i])
        width = int(data["width"][i])
        height = int(data["height"][i])
        abs_x = roi["x"] + left
        abs_y = roi["y"] + top
        normalized = normalize_text(text)
        items.append({
            "text": text,
            "normalizedText": normalized,
            "confidence": conf,
            "x": abs_x,
            "y": abs_y,
            "w": width,
            "h": height,
            "centerX": abs_x + (width / 2.0),
            "centerY": abs_y + (height / 2.0),
            "lineNum": int(data.get("line_num", [0] * item_count)[i] or 0),
            "blockNum": int(data.get("block_num", [0] * item_count)[i] or 0),
            "parNum": int(data.get("par_num", [0] * item_count)[i] or 0),
            "source": "word",
        })
    return items


def build_word_items_from_rapidocr(results: Any, roi: Dict[str, Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    if not results:
        return items

    for idx, entry in enumerate(results):
        if not isinstance(entry, (list, tuple)) or len(entry) < 2:
            continue
        points = entry[0]
        payload = entry[1]
        if not points or not payload:
            continue

        text = ""
        conf = -1.0
        if isinstance(payload, (list, tuple)):
            if len(payload) >= 1:
                text = str(payload[0] or "").strip()
            if len(payload) >= 2:
                conf = safe_float(payload[1], default=-1.0)
        else:
            text = str(payload or "").strip()

        if not text:
            continue

        xs = [int(round(p[0])) for p in points if isinstance(p, (list, tuple)) and len(p) >= 2]
        ys = [int(round(p[1])) for p in points if isinstance(p, (list, tuple)) and len(p) >= 2]
        if not xs or not ys:
            continue

        left = min(xs)
        top = min(ys)
        right = max(xs)
        bottom = max(ys)
        width = max(1, right - left)
        height = max(1, bottom - top)
        abs_x = roi["x"] + left
        abs_y = roi["y"] + top
        normalized = normalize_text(text)

        items.append({
            "text": text,
            "normalizedText": normalized,
            "confidence": conf,
            "x": abs_x,
            "y": abs_y,
            "w": width,
            "h": height,
            "centerX": abs_x + (width / 2.0),
            "centerY": abs_y + (height / 2.0),
            "lineNum": idx + 1,
            "blockNum": 1,
            "parNum": 1,
            "source": "line",
            "polygon": [[roi["x"] + int(round(p[0])), roi["y"] + int(round(p[1]))] for p in points if isinstance(p, (list, tuple)) and len(p) >= 2],
        })
    return items


def aggregate_items(word_items: List[Dict[str, Any]], group_by: str) -> List[Dict[str, Any]]:
    if group_by == "word":
        return [dict(item) for item in word_items]

    groups: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = {}
    for idx, item in enumerate(word_items):
        if group_by == "line":
            key = (item.get("blockNum"), item.get("parNum"), item.get("lineNum"))
        else:
            bucket = item.get("lineNum")
            key = (item.get("blockNum"), item.get("parNum"), bucket)
        groups.setdefault(key, []).append({**item, "_idx": idx})

    aggregated: List[Dict[str, Any]] = []
    for key, group in groups.items():
        ordered = sorted(group, key=lambda entry: (entry.get("x", 0), entry.get("_idx", 0)))
        text = " ".join((entry.get("text") or "").strip() for entry in ordered if (entry.get("text") or "").strip()).strip()
        if not text:
            continue
        xs = [int(entry["x"]) for entry in ordered]
        ys = [int(entry["y"]) for entry in ordered]
        rights = [int(entry["x"]) + int(entry["w"]) for entry in ordered]
        bottoms = [int(entry["y"]) + int(entry["h"]) for entry in ordered]
        left = min(xs)
        top = min(ys)
        right = max(rights)
        bottom = max(bottoms)
        width = max(1, right - left)
        height = max(1, bottom - top)
        confidences = [safe_float(entry.get("confidence"), default=-1.0) for entry in ordered if safe_float(entry.get("confidence"), default=-1.0) >= 0]
        confidence = sum(confidences) / len(confidences) if confidences else -1.0
        normalized = normalize_text(text)
        aggregated.append({
            "text": text,
            "normalizedText": normalized,
            "confidence": confidence,
            "x": left,
            "y": top,
            "w": width,
            "h": height,
            "centerX": left + (width / 2.0),
            "centerY": top + (height / 2.0),
            "lineNum": key[2] if len(key) >= 3 else 0,
            "blockNum": key[0] if len(key) >= 1 else 0,
            "parNum": key[1] if len(key) >= 2 else 0,
            "source": group_by,
            "parts": [{k: v for k, v in entry.items() if k in WORD_KEYS} for entry in ordered],
        })
    return aggregated


def choose_group_mode(group_by: str, engine_name: str, query: str = "") -> str:
    if group_by != "auto":
        return group_by
    normalized_query = normalize_text(query)
    if engine_name == "rapidocr":
        return "phrase"
    if " " in normalized_query:
        return "line"
    return "word"


def sort_match_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (
            -(safe_float(item.get("confidence"), default=-1.0)),
            item.get("y", 0),
            item.get("x", 0),
            -(len(item.get("normalizedText") or "")),
        ),
    )


def build_debug_overlay(image: Image.Image, items: List[Dict[str, Any]], output_path: Path) -> str:
    overlay = image.convert("RGB").copy()
    draw = ImageDraw.Draw(overlay)
    for idx, item in enumerate(items, start=1):
        x = int(item.get("x", 0))
        y = int(item.get("y", 0))
        w = max(1, int(item.get("w", 1)))
        h = max(1, int(item.get("h", 1)))
        color = (255, 0, 0) if idx == 1 else (255, 165, 0)
        draw.rectangle((x, y, x + w, y + h), outline=color, width=2)
        label = f"{idx}:{item.get('text', '')[:24]}"
        text_y = max(0, y - 14)
        draw.rectangle((x, text_y, min(overlay.width - 1, x + max(40, len(label) * 7)), min(overlay.height - 1, text_y + 14)), fill=(0, 0, 0))
        draw.text((x + 2, text_y), label, fill=(255, 255, 0))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    overlay.save(output_path)
    return str(output_path)


def try_rapidocr(processed_image: Image.Image) -> Tuple[str, str, str, List[Dict[str, Any]], str]:
    try:
        from rapidocr_onnxruntime import RapidOCR  # type: ignore
    except Exception as exc:
        raise OcrEngineError(f"RapidOCR unavailable: {exc}") from exc

    try:
        engine = RapidOCR()
        results, _ = engine(processed_image)
        word_items = build_word_items_from_rapidocr(results, {"x": 0, "y": 0})
        return "rapidocr", getattr(sys.modules.get("rapidocr_onnxruntime"), "__version__", "unknown"), "RapidOCR ONNXRuntime", word_items, "ok"
    except Exception as exc:
        raise OcrEngineError(f"RapidOCR failed: {exc}") from exc


def default_tessdata_dir() -> Optional[Path]:
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parent / "third_party" / "tessdata",
        Path(r"C:\Program Files\Tesseract-OCR\tessdata"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def configure_tesseract() -> Tuple[str, Optional[str]]:
    tesseract_cmd = os.environ.get("TESSERACT_CMD") or r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    tessdata_dir = os.environ.get("TESSDATA_PREFIX")
    if not tessdata_dir:
        detected = default_tessdata_dir()
        if detected is not None:
            tessdata_dir = str(detected)
            os.environ["TESSDATA_PREFIX"] = tessdata_dir
    if Path(tesseract_cmd).exists():
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    return pytesseract.pytesseract.tesseract_cmd, tessdata_dir


def choose_tesseract_psm(lang: str, roi: Dict[str, Any], requested_psm: str) -> str:
    requested = (requested_psm or "auto").strip().lower()
    if requested and requested != "auto":
        return requested

    normalized_lang = (lang or "").lower()
    contains_chinese = any(token in normalized_lang for token in ("chi_sim", "chi_tra", "chi", "zh", "chinese"))
    area = int(roi.get("width", 0) or 0) * int(roi.get("height", 0) or 0)
    if contains_chinese and area >= 1_000_000:
        return "12"
    if contains_chinese:
        return "6"
    return "3"


def run_tesseract(processed_image: Image.Image, roi: Dict[str, Any], lang: str, requested_psm: str = "auto") -> Tuple[str, str, str, str, List[Dict[str, Any]]]:
    tesseract_cmd, tessdata_dir = configure_tesseract()
    psm = choose_tesseract_psm(lang, roi, requested_psm)
    config_parts: List[str] = []
    if tessdata_dir:
        safe_tessdata_dir = str(Path(tessdata_dir).resolve())
        os.environ["TESSDATA_PREFIX"] = safe_tessdata_dir
        config_parts.extend(["--tessdata-dir", safe_tessdata_dir])
    if psm:
        config_parts.extend(["--psm", psm])
    config = " ".join(config_parts)
    full_text = pytesseract.image_to_string(processed_image, lang=lang, config=config)
    data = pytesseract.image_to_data(processed_image, lang=lang, output_type=Output.DICT, config=config)
    detail = tesseract_cmd if not tessdata_dir else f"{tesseract_cmd} | tessdata={tessdata_dir} | psm={psm}"
    word_items = build_word_items_from_tesseract(data, roi)
    return "tesseract", "pytesseract", detail, full_text, word_items


def remap_items_to_abs(items: List[Dict[str, Any]], roi: Dict[str, Any]) -> List[Dict[str, Any]]:
    remapped: List[Dict[str, Any]] = []
    for item in items:
        clone = dict(item)
        clone["x"] = roi["x"] + int(item.get("x", 0))
        clone["y"] = roi["y"] + int(item.get("y", 0))
        clone["centerX"] = clone["x"] + (int(item.get("w", 0)) / 2.0)
        clone["centerY"] = clone["y"] + (int(item.get("h", 0)) / 2.0)
        if item.get("polygon"):
            clone["polygon"] = [[roi["x"] + int(p[0]), roi["y"] + int(p[1])] for p in item["polygon"]]
        remapped.append(clone)
    return remapped


def main() -> int:
    args = parse_args()
    image_path = Path(args.image_path).expanduser()
    lang = args.lang.strip() if args.lang and args.lang.strip() else DEFAULT_LANG
    top_n = max(1, int(args.top_n or DEFAULT_TOP_N))

    if not image_path.exists():
        print(json.dumps({"ok": False, "error": f"image not found: {image_path}"}, ensure_ascii=False))
        return 1

    try:
        original_image = Image.open(image_path)
        roi_image, roi = clamp_roi(original_image, args.x, args.y, args.width, args.height)
        processed_image = apply_preprocess(roi_image, args.preprocess)
        normalized_query = normalize_text(args.query or "")

        engine_attempts: List[Dict[str, Any]] = []
        engine_name = ""
        engine_version = ""
        engine_detail = ""
        full_text = ""
        raw_word_items: List[Dict[str, Any]] = []

        normalized_lang = (lang or "").lower()
        contains_chinese = any(token in normalized_lang for token in ("chi_sim", "chi_tra", "chi", "zh", "chinese"))
        preferred_engine = args.engine
        if preferred_engine == "auto":
            preferred_engine = "tesseract" if contains_chinese else "rapidocr"

        if preferred_engine == "tesseract":
            try:
                tess_engine, tess_version, tess_detail, full_text, raw_word_items = run_tesseract(processed_image, roi, lang, args.psm)
                engine_name = tess_engine
                engine_version = tess_version
                engine_detail = tess_detail
                engine_attempts.append({"engine": tess_engine, "ok": True, "detail": tess_detail, "status": "ok", "version": tess_version})
            except Exception as tess_exc:
                engine_attempts.append({
                    "engine": "tesseract",
                    "ok": False,
                    "detail": str(tess_exc),
                    "status": "fallback_to_rapidocr",
                })
                rapid_engine, rapid_version, rapid_detail, rapid_items, rapid_status = try_rapidocr(processed_image)
                engine_attempts.append({"engine": rapid_engine, "ok": True, "detail": rapid_detail, "status": rapid_status, "version": rapid_version})
                engine_name = rapid_engine
                engine_version = rapid_version
                engine_detail = rapid_detail
                full_text = "\n".join(item.get("text", "") for item in rapid_items)
                raw_word_items = remap_items_to_abs(rapid_items, roi)
        else:
            try:
                rapid_engine, rapid_version, rapid_detail, rapid_items, rapid_status = try_rapidocr(processed_image)
                engine_attempts.append({"engine": rapid_engine, "ok": True, "detail": rapid_detail, "status": rapid_status, "version": rapid_version})
                engine_name = rapid_engine
                engine_version = rapid_version
                engine_detail = rapid_detail
                full_text = "\n".join(item.get("text", "") for item in rapid_items)
                raw_word_items = remap_items_to_abs(rapid_items, roi)
            except Exception as rapid_exc:
                engine_attempts.append({
                    "engine": "rapidocr",
                    "ok": False,
                    "detail": str(rapid_exc),
                    "status": "fallback_to_tesseract",
                })
                tess_engine, tess_version, tess_detail, full_text, raw_word_items = run_tesseract(processed_image, roi, lang, args.psm)
                engine_name = tess_engine
                engine_version = tess_version
                engine_detail = tess_detail
                engine_attempts.append({"engine": tess_engine, "ok": True, "detail": tess_detail, "status": "ok", "version": tess_version})

        effective_group_by = choose_group_mode(args.group_by, engine_name, args.query or "")
        aggregated_items = aggregate_items(raw_word_items, effective_group_by)
        matched_items = [
            item for item in aggregated_items
            if item_matches(item.get("normalizedText", ""), normalized_query, args.query_mode)
        ]
        matched_items = sort_match_items(matched_items)
        top_matches = matched_items[:top_n]

        debug_overlay_path: Optional[str] = None
        if args.debug_overlay:
            debug_overlay_path = build_debug_overlay(original_image, top_matches, Path(args.debug_overlay).expanduser())

        result = {
            "ok": True,
            "image": str(image_path),
            "lang": lang,
            "engine": {
                "name": engine_name,
                "version": engine_version,
                "detail": engine_detail,
                "attempts": engine_attempts,
                "preferred": preferred_engine,
                "fallback": "rapidocr" if preferred_engine == "tesseract" else "tesseract",
                "selectedGroupBy": effective_group_by,
            },
            "tesseract": pytesseract.pytesseract.tesseract_cmd,
            "preprocess": args.preprocess,
            "query": args.query or None,
            "queryMode": args.query_mode,
            "groupBy": args.group_by,
            "effectiveGroupBy": effective_group_by,
            "topN": top_n,
            "roi": roi,
            "text": full_text,
            "normalizedText": normalize_text(full_text),
            "count": len(matched_items),
            "items": matched_items,
            "matches": top_matches,
            "debugOverlay": debug_overlay_path,
            "allItemsCount": len(aggregated_items),
        }
        safe_print_json(result)
        return 0
    except Exception as exc:
        safe_print_json({
            "ok": False,
            "error": str(exc),
            "traceback": traceback.format_exc(limit=3),
        })
        return 1


def safe_print_json(payload: Dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    try:
        sys.stdout.write(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
        try:
            sys.stdout.buffer.flush()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
