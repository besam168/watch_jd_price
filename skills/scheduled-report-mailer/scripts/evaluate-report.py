from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = SKILL_ROOT / "config" / "report-config.json"
OUT_STATUS = SKILL_ROOT / "state" / "report-evaluation.json"

KEYWORD_MAP = {
    "gaza": ["加沙", "gaza", "哈马斯"],
    "ukraine": ["乌克兰", "ukraine", "俄乌", "russia-ukraine"],
    "us-china-trade": ["中美经贸", "中美关系", "trade", "tariff", "china", "美国关税"],
    "us-equities": ["S&P 500", "纳斯达克", "道琼斯", "美股"],
    "gold": ["黄金", "gold", "XAU"],
    "brent": ["布伦特", "brent"]
}

INTERNATIONAL_CURRENT_AFFAIRS_KEYWORDS = [
    "国际", "全球", "外交", "地缘", "中东", "加沙", "以色列", "伊朗", "乌克兰", "俄乌",
    "美国", "中国", "中美", "关税", "贸易", "经贸", "欧盟", "欧洲", "英国", "日本",
    "韩国", "台湾", "航运", "能源", "原油", "黄金", "市场", "风险", "制裁", "谈判"
]

MAIN_HEADLINE_SECTION_MARKERS = [
    "一、重要头条新闻",
    "📊 实时头条（过去24-48小时）",
    "📊 实时头条",
]

MAIN_HEADLINE_SECTION_END_MARKERS = [
    "二、AI科技专栏头条",
    "二、",
    "三、全球市场动态",
    "🌍 地缘政治分析",
    "📈 金融市场速报",
]

SOURCE_LINE_RE = re.compile(r"（来源：.+?\|\s*发布时间：.+?）")
HEADLINE_LINE_RE = re.compile(r"^\s*(\d+)\.\s+(.+?)\s*$")


def extract_main_headline_block(text: str) -> str:
    for start_marker in MAIN_HEADLINE_SECTION_MARKERS:
        if start_marker in text:
            after = text.split(start_marker, 1)[1]
            for marker in MAIN_HEADLINE_SECTION_END_MARKERS:
                if marker in after:
                    return after.split(marker, 1)[0]
            return after
    return ""


def parse_main_headlines(text: str) -> list[dict]:
    block = extract_main_headline_block(text)
    if not block.strip():
        return []

    lines = [line.rstrip() for line in block.splitlines()]
    items: list[dict] = []
    current: dict | None = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        m = HEADLINE_LINE_RE.match(line)
        if m:
            if current:
                items.append(current)
            current = {
                "index": int(m.group(1)),
                "title": m.group(2).strip(),
                "lines": [line],
            }
            continue
        if current is not None:
            current["lines"].append(line)

    if current:
        items.append(current)

    normalized: list[dict] = []
    for item in items:
        body = "\n".join(item["lines"])
        has_source_time = bool(SOURCE_LINE_RE.search(body))
        keyword_hits = [kw for kw in INTERNATIONAL_CURRENT_AFFAIRS_KEYWORDS if kw.lower() in body.lower()]
        normalized.append(
            {
                "index": item["index"],
                "title": item["title"],
                "hasSourceAndTime": has_source_time,
                "matchedKeywords": keyword_hits,
                "isInternationalCurrentAffairsCandidate": has_source_time and bool(keyword_hits),
            }
        )
    return normalized


def main() -> int:
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    must_check = cfg.get("collection_policy", {}).get("must_check", [])
    report_path = ROOT / cfg.get("paths", {}).get("latest_report_txt", "reports/scheduled/latest_report.txt")
    evidence_path = ROOT / "reports" / "scheduled" / "latest_report_evidence.json"
    text = report_path.read_text(encoding="utf-8", errors="replace") if report_path.exists() else ""

    checks = {}
    for item in must_check:
        keywords = KEYWORD_MAP.get(item, [item])
        matched = [kw for kw in keywords if kw.lower() in text.lower()]
        checks[item] = {
            "ok": bool(matched),
            "matchedKeywords": matched,
        }

    evidence = {}
    if evidence_path.exists():
        try:
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        except Exception:
            evidence = {}

    main_headlines = parse_main_headlines(text)
    candidate_headlines = [item for item in main_headlines if item["isInternationalCurrentAffairsCandidate"]]
    content_coverage_ok = len(candidate_headlines) >= 1

    headline_gate_ok = bool(
        evidence.get("headlineEvidenceCount", 0) >= 1
        and not evidence.get("hasPlaceholderSearchDiscovery", False)
    )

    result = {
        "generatedAt": datetime.now().isoformat(),
        "reportPath": str(report_path),
        "mustCheckResults": checks,
        "contentCoverageGate": {
            "ok": content_coverage_ok,
            "mainHeadlineCount": len(main_headlines),
            "internationalCurrentAffairsCandidateCount": len(candidate_headlines),
            "candidateTitles": [item["title"] for item in candidate_headlines[:8]],
        },
        "headlineEvidenceGate": {
            "ok": headline_gate_ok,
            "headlineCount": evidence.get("headlineCount", 0),
            "headlineEvidenceCount": evidence.get("headlineEvidenceCount", 0),
            "hasPlaceholderSearchDiscovery": evidence.get("hasPlaceholderSearchDiscovery", False),
        },
        "summary": {
            "okCount": sum(1 for v in checks.values() if v["ok"]),
            "total": len(checks),
            "anchorMissing": [k for k, v in checks.items() if not v["ok"]],
        },
    }
    OUT_STATUS.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(OUT_STATUS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
