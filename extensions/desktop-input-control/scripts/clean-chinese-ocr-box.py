#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
import unicodedata
from typing import Any, Dict, List


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = re.sub(r"\s+", " ", value).strip()
    return value.lower()


def is_ascii_like(text: str) -> bool:
    s = text or ""
    if not s:
        return True
    ascii_count = sum(1 for ch in s if ord(ch) < 128)
    return ascii_count / max(1, len(s)) >= 0.7


def looks_like_noise(text: str) -> bool:
    s = (text or "").strip()
    if not s:
        return True
    if re.fullmatch(r"[-_./:=+()\[\]{}<>|\\]+", s):
        return True
    return False


def part_score(part: Dict[str, Any]) -> float:
    text = part.get("text", "") or ""
    conf = float(part.get("confidence", 0.0) or 0.0)
    x = float(part.get("x", 0.0) or 0.0)

    score = conf
    if not is_ascii_like(text):
        score += 35.0
    if looks_like_noise(text):
        score -= 50.0
    if any(ord(ch) > 127 for ch in text):
        score += 15.0
    score -= x * 0.002
    return score


def cluster_parts(parts: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    if not parts:
        return []
    ordered = sorted(parts, key=lambda p: (float(p.get("x", 0)), float(p.get("centerY", 0))))
    clusters: List[List[Dict[str, Any]]] = [[ordered[0]]]
    for part in ordered[1:]:
        prev = clusters[-1][-1]
        prev_right = float(prev.get("x", 0)) + float(prev.get("w", 0))
        gap = float(part.get("x", 0)) - prev_right
        y_delta = abs(float(part.get("centerY", 0)) - float(prev.get("centerY", 0)))
        h_ref = max(float(prev.get("h", 1)), float(part.get("h", 1)))
        if gap <= max(26.0, h_ref * 0.8) and y_delta <= max(18.0, h_ref * 0.6):
            clusters[-1].append(part)
        else:
            clusters.append([part])
    return clusters


def cluster_score(cluster: List[Dict[str, Any]]) -> float:
    if not cluster:
        return -1e9
    score = sum(part_score(p) for p in cluster)
    text = "".join((p.get("text", "") or "") for p in cluster)
    width = max(float(p.get("x", 0)) + float(p.get("w", 0)) for p in cluster) - min(float(p.get("x", 0)) for p in cluster)
    score += min(40.0, len(text) * 6.0)
    if not is_ascii_like(text):
        score += 25.0
    if width > 260:
        score -= 25.0
    return score


def cluster_to_box(cluster: List[Dict[str, Any]]) -> Dict[str, Any]:
    left = min(float(p.get("x", 0)) for p in cluster)
    top = min(float(p.get("y", 0)) for p in cluster)
    right = max(float(p.get("x", 0)) + float(p.get("w", 0)) for p in cluster)
    bottom = max(float(p.get("y", 0)) + float(p.get("h", 0)) for p in cluster)
    width = max(1.0, right - left)
    height = max(1.0, bottom - top)
    text = " ".join((p.get("text", "") or "").strip() for p in cluster if (p.get("text", "") or "").strip())
    confidences = [float(p.get("confidence", 0.0) or 0.0) for p in cluster]
    return {
        "text": text,
        "normalizedText": normalize_text(text),
        "confidence": round(sum(confidences) / max(1, len(confidences)), 2),
        "x": round(left, 2),
        "y": round(top, 2),
        "w": round(width, 2),
        "h": round(height, 2),
        "centerX": round(left + width / 2.0, 2),
        "centerY": round(top + height / 2.0, 2),
        "parts": cluster,
    }


def clean_chinese_target_box(item: Dict[str, Any]) -> Dict[str, Any]:
    parts = item.get("parts") or []
    if not parts:
        return {"mode": "passthrough", "box": item, "clusters": []}

    clusters = cluster_parts(parts)
    scored = [{"cluster": c, "score": cluster_score(c), "box": cluster_to_box(c)} for c in clusters]
    scored.sort(key=lambda e: e["score"], reverse=True)
    best = scored[0] if scored else None
    if not best:
        return {"mode": "passthrough", "box": item, "clusters": []}

    return {
        "mode": "cluster_cleaned",
        "box": best["box"],
        "clusters": [
            {
                "score": round(entry["score"], 2),
                "box": entry["box"],
            }
            for entry in scored
        ],
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Clean noisy OCR boxes for Chinese small targets")
    parser.add_argument("json_file")
    args = parser.parse_args()

    payload = json.loads(open(args.json_file, "r", encoding="utf-8").read())
    item = payload.get("item") or payload
    result = clean_chinese_target_box(item)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
