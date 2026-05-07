import argparse
import json
import os
import re
import shutil
import sys
import time
import traceback
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_DIR = ROOT / "repo"
BRIDGE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BRIDGE_DIR / "outputs"
HISTORY_DIR = OUTPUT_DIR / "history"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_DIR.mkdir(parents=True, exist_ok=True)
STATUS_PATH = OUTPUT_DIR / "latest-status.json"
RESULT_MD_PATH = OUTPUT_DIR / "latest-result.md"
RESULT_JSON_PATH = OUTPUT_DIR / "latest-result.json"
LOG_PATH = OUTPUT_DIR / "latest-run.log"
PROFILES_PATH = BRIDGE_DIR / "provider_profiles.json"
PROFILES_EXAMPLE_PATH = BRIDGE_DIR / "provider_profiles.example.json"
CONFIG_PATH = BRIDGE_DIR / "bridge-config.json"
CONFIG_EXAMPLE_PATH = BRIDGE_DIR / "bridge-config.example.json"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def ts_slug():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def write_json(path: Path, data: dict):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path, default: dict):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def classify_error(msg: str) -> str:
    text = (msg or "").lower()
    if "timeout" in text or "timed out" in text or "timeoutexpired" in text:
        return "timeout_error"
    if "no module named" in text or "modulenotfounderror" in text or "importerror" in text:
        return "install_error"
    if "api_key" in text or "auth" in text or "unauthorized" in text or "401" in text or "403" in text:
        return "provider_auth_error"
    if "quota" in text or "resource_exhausted" in text or "429" in text:
        return "provider_quota_error"
    if "502" in text or "503" in text or "bad gateway" in text or "cloudflare" in text:
        return "provider_gateway_error"
    if "ssl" in text or "decryption_failed_or_bad_record_mac" in text:
        return "network_ssl_error"
    if "pip" in text:
        return "install_error"
    if "output" in text and "write" in text:
        return "output_write_error"
    return "runtime_error"


def should_retry(error_type: str) -> bool:
    return error_type in {"provider_gateway_error", "network_ssl_error"}


def load_profiles() -> dict:
    source = None
    if PROFILES_PATH.exists():
        source = PROFILES_PATH
    elif PROFILES_EXAMPLE_PATH.exists():
        source = PROFILES_EXAMPLE_PATH
    if not source:
        raise FileNotFoundError("provider profiles file not found")
    return json.loads(source.read_text(encoding="utf-8"))


def load_profile(profile_name: str | None) -> dict:
    if not profile_name:
        return {}
    data = load_profiles()
    if profile_name not in data:
        raise KeyError(f"profile not found: {profile_name}")
    return data[profile_name]


def load_bridge_config() -> dict:
    if CONFIG_PATH.exists():
        return load_json(CONFIG_PATH, {})
    return load_json(CONFIG_EXAMPLE_PATH, {})


def resolve_profile_list(primary_profile: str | None) -> list[str]:
    cfg = load_bridge_config()
    profiles = load_profiles()
    default_profile = cfg.get("defaultProfile") or "hi_code_gpt54"
    chosen = primary_profile or default_profile
    order = [chosen]
    fallback_profile = cfg.get("fallbackProfile")
    chosen_profile = profiles.get(chosen, {}) if chosen else {}
    fallback_profile_data = profiles.get(fallback_profile, {}) if fallback_profile else {}
    chosen_provider = (chosen_profile.get("provider") or "").lower()
    fallback_provider = (fallback_profile_data.get("provider") or "").lower()
    if (
        fallback_profile
        and fallback_profile in profiles
        and fallback_profile not in order
        and chosen_provider == fallback_provider
    ):
        order.append(fallback_profile)
    return order


def resolve_run_params(args, profile_name: str) -> dict:
    app_cfg = load_bridge_config()
    profile = load_profile(profile_name)
    provider = args.provider or profile.get("provider") or "openai"
    model = args.model or profile.get("model") or "gpt-5.4"
    base_url = args.base_url or profile.get("base_url")
    env_key = profile.get("env_key")
    api_key = None
    if args.api_key:
        api_key = args.api_key
    elif env_key:
        api_key = os.getenv(env_key)
        if not api_key:
            api_key = profile.get("api_key")
    api_version = profile.get("api_version")
    transport = profile.get("transport")
    default_analysts = app_cfg.get("defaultAnalysts") or ["market"]
    analysts = [a.strip() for a in args.analysts.split(",") if a.strip()] if args.analysts else default_analysts
    language = args.language or app_cfg.get("defaultLanguage") or "zh-CN"
    save_history = bool(app_cfg.get("saveHistory", True)) if args.save_history is None else args.save_history
    retry_count = int(app_cfg.get("retryCount", 1)) if args.retry_count is None else int(args.retry_count)
    retry_wait_seconds = int(app_cfg.get("retryWaitSeconds", 10)) if args.retry_wait_seconds is None else int(args.retry_wait_seconds)
    return {
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "api_key": api_key,
        "env_key": env_key,
        "api_version": api_version,
        "transport": transport,
        "profile": profile_name,
        "analysts": analysts,
        "language": language,
        "save_history": save_history,
        "retry_count": retry_count,
        "retry_wait_seconds": retry_wait_seconds,
    }


def extract_decision_core(decision: str) -> str:
    text = (decision or "").replace("\r\n", "\n")
    upper = text.upper()

    start_markers = [
        "FINAL TRANSACTION PROPOSAL:",
        "FINAL DECISION:",
        "FINAL TRANSACTION:",
    ]
    start = 0
    for marker in start_markers:
        idx = upper.find(marker)
        if idx >= 0:
            start = idx
            break

    snippet = text[start:] if start < len(text) else text

    end_markers = [
        "BRIDGE_OK ",
        "BRIDGE_FAIL ",
        "TRACEBACK ",
    ]
    end = len(snippet)
    upper_snippet = snippet.upper()
    for marker in end_markers:
        idx = upper_snippet.find(marker)
        if idx >= 0:
            end = min(end, idx)
    snippet = snippet[:end]
    return snippet.strip()


def normalize_decision_label(decision: str) -> str:
    core = extract_decision_core(decision)
    patterns = [
        r"FINAL\s+TRANSACTION\s+PROPOSAL\s*:\s*\*\*(BUY|HOLD|SELL)\*\*",
        r"FINAL\s+TRANSACTION\s+PROPOSAL\s*:\s*(BUY|HOLD|SELL)\b",
        r"FINAL\s+DECISION\s*:\s*\*\*(BUY|HOLD|SELL)\*\*",
        r"FINAL\s+DECISION\s*:\s*(BUY|HOLD|SELL)\b",
    ]
    for pattern in patterns:
        m = re.search(pattern, core, flags=re.IGNORECASE)
        if m:
            return m.group(1).upper()

    text = core.upper()
    if "HOLD" in text:
        return "HOLD"
    if "SELL" in text:
        return "SELL"
    if "BUY" in text:
        return "BUY"
    return core.strip().splitlines()[0][:40] if core.strip() else "UNKNOWN"


def clean_text_line(line: str) -> str:
    text = (line or "").replace("\uFFFD", "").strip()
    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\u4e00-\u9fff]+", " ", text)
    text = re.sub(r"^[\-•*\d\.)\(\s#]+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -•\t")


def split_decision_lines(decision: str) -> list[str]:
    core = extract_decision_core(decision)
    lower_core = core.lower()
    key_idx = lower_core.find("key reasons:")
    risk_idx = lower_core.find("risk management")
    if key_idx >= 0:
        core = core[key_idx:]
    elif risk_idx >= 0:
        core = core[risk_idx:]

    raw_lines = core.splitlines()
    lines = []
    for raw in raw_lines:
        text = clean_text_line(raw)
        if not text:
            continue
        low = text.lower()
        if low in {"buy", "sell", "hold", "continue", "key reasons:", "actionable view:", "bottom line"}:
            continue
        if low.startswith("final transaction proposal"):
            continue
        if low.startswith("for ") and " as of " in low:
            continue
        if low.startswith("these are the most relevant because"):
            continue
        if low.startswith("the most relevant because"):
            continue
        if low.startswith("this is a strong non-redundant combination"):
            continue
        if low.startswith("indicator set i selected"):
            continue
        if low.startswith("indicator:"):
            continue
        if any(token in low for token in ["close_10_ema", "close_50_sma", "close_200_sma", "macd", "macdh", "rsi", "atr", "vwma"]):
            if len(text) <= 80:
                continue
        if low in {"price action context from raw stock data", "actionable trading insights", "risk management view"}:
            continue
        lines.append(text)
    return lines


def is_mostly_numeric_line(text: str) -> bool:
    letters = sum(ch.isalpha() for ch in text)
    digits = sum(ch.isdigit() for ch in text)
    return digits >= 3 and letters <= 8


def zhify_reason(text: str) -> str:
    out = clean_text_line(text)
    low = out.lower()

    custom_rules = [
        (r"sma\s*\+\s*200 sma.*medium.*long-term trend structure", "中长期均线结构仍偏弱，趋势修复基础并不扎实"),
        (r"ema: gives a faster read on the recent rebound and whether it is fading", "短线均线显示这轮反弹正在降速，延续性不足"),
        (r"rsi: checks whether price is stretched or merely recovering from oversold", "RSI 只说明超跌修复过，但还不足以确认新的强势上升趋势"),
        (r"atr: essential because tsla is high-volatility and risk sizing matters", "TSLA 波动本来就大，仓位控制和止损空间必须更保守"),
        (r"macd.*still positive.*declining|macd.*deteriorating", "MACD 虽然没有彻底转坏，但边际动能已经走弱"),
        (r"price slipping back below the 10-day ema.*50-day sma", "价格重新回到 10 日均线下方，而且在 50 日均线附近受阻，说明买盘控制力不足"),
        (r"rebound appears to have lost momentum quickly", "这轮反弹很快失去动能，更像情绪性修复而不是趋势反转"),
        (r"well below a falling 200-day sma", "价格仍明显压在下行中的 200 日均线下方，大趋势依旧偏空"),
        (r"bullish case depends more on future narrative improvement", "当前多头逻辑更多是在赌后续故事，而不是已有技术面确认"),
        (r"trim or exit into strength", "如果已有仓位，更合理的做法是趁反弹分批减仓或退出"),
        (r"do not initiate new long positions here", "这个位置不适合再开新的多头仓位"),
        (r"failed bounce into resistance", "如果反弹到阻力位再次转弱，会是更清晰的风险信号"),
        (r"clear technical breakdown", "若后续出现明确破位，下行空间会被进一步打开"),
        (r"retest of lower support zones", "一旦重新转弱，后面大概率还要回踩更低支撑区"),
        (r"trend across 3 horizons", "短中长期三个周期一起看，当前都还没形成强势共振"),
        (r"momentum direction and momentum change", "动量方向已经转弱，边际变化也不支持继续追多"),
        (r"mean-reversion/extremes", "超跌反弹的边际优势已经消耗，均值回归带来的红利在减弱"),
        (r"volume confirmation", "成交量曾经确认过反弹，但最新量价配合已经不支持继续强攻"),
        (r"short-term: rebound remains partially intact, but fading", "短线反弹结构还没完全破坏，但力度已经明显衰减"),
        (r"a stock below a falling 10 ema after a vertical rally often enters either", "急拉后重新跌回下行中的 10 日均线下方，通常意味着后面更容易转入震荡走弱"),
        (r"fail below it = likely opens room for a retest of lower support zones", "如果继续站不回关键均线，后面大概率会去回踩更低支撑"),
    ]
    for pattern, replacement in custom_rules:
        if re.search(pattern, low):
            return replacement

    replacements = [
        (r"the most important fact is that .* remains far below (?:its |the )?200-day sma", "最关键的问题是，价格仍明显低于 200 日均线"),
        (r"big-picture trend: still structurally weak", "大趋势仍偏弱，整体结构没有修复"),
        (r"long-term trend is still bearish", "长期趋势仍偏空"),
        (r"medium-term trend: flattening, but not convincingly bullish", "中期趋势趋于走平，但还谈不上明确转强"),
        (r"short-term trend: rebound has lost some momentum", "短线反弹动能正在减弱"),
        (r"bullish momentum is fading", "多头动能正在走弱"),
        (r"the rebound is losing force", "这轮反弹的力量在减弱"),
        (r"post-rally consolidation", "上涨后的整理阶段"),
        (r"still far below (?:its |the )?200-day sma", "价格仍明显低于 200 日均线"),
        (r"trading roughly 20%\+? below the 200-day sma", "当前价格较 200 日均线仍低约 20%"),
        (r"below the short-term ema", "价格已经回到短期均线下方"),
        (r"below the vwma", "价格回到成交量加权均线下方"),
        (r"rsi.*neutral", "RSI 处于中性区间，暂未出现强趋势确认"),
        (r"macd.*decelerating", "MACD 虽仍有修复迹象，但上行动能在放缓"),
        (r"high-volatility trading vehicle", "波动仍然偏大，交易容错要求更高"),
        (r"wide stops are necessary", "若参与，止损不能设得过紧"),
        (r"position sizing should be more conservative", "仓位应适当保守"),
        (r"decision point", "当前正处在方向选择节点"),
    ]
    for pattern, replacement in replacements:
        if re.search(pattern, low):
            return replacement

    out = re.sub(r"\*+", "", out)
    out = re.sub(r"`", "", out)
    out = re.sub(r"\s+", " ", out).strip(" .:;-")
    if re.fullmatch(r"[A-Za-z0-9_\-/ ,\+\(\)]+", out):
        return f"{out}（原文要点，待进一步细化）"
    return out[:120]


def zh_decision_label(decision: str) -> str:
    return {
        "BUY": "偏多",
        "HOLD": "观望",
        "SELL": "偏空",
        "ERROR": "运行失败",
        "UNKNOWN": "未明确",
    }.get((decision or "").upper(), decision or "未明确")


def summarize_zh(decision: str, ticker: str, trade_date: str, provider: str, model: str, analysts: list[str], key_reasons: list[str], risks: list[str]) -> str:
    decision_label = normalize_decision_label(decision)
    decision_zh = zh_decision_label(decision_label)
    reasons_zh = [zhify_reason(x) for x in key_reasons[:2]]
    risks_zh = [zhify_reason(x) for x in risks[:1]]
    parts = [
        f"{ticker} 在 {trade_date} 的桥接分析已完成。",
        f"当前路由：{provider}/{model}；分析模式：{','.join(analysts)}。",
        f"结论：{decision_zh}（{decision_label}）。",
    ]
    if reasons_zh:
        parts.append(f"核心依据：{'；'.join(reasons_zh)}。")
    if risks_zh:
        parts.append(f"主要风险：{'；'.join(risks_zh)}。")
    return "".join(parts)


def ensure_chinese_bullets(items: list[str], kind: str) -> list[str]:
    rows = []
    seen = set()
    for item in items or []:
        text = zhify_reason(item)
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        rows.append(text)
    if rows:
        return rows
    if kind == "reason":
        return ["暂未稳定提炼到中文依据"]
    return ["暂未稳定提炼到中文风险"]


def extract_key_reasons(decision: str) -> list[str]:
    core = extract_decision_core(decision)
    bullet_matches = re.findall(r"^\s*[-*]\s+(.+)$", core, flags=re.MULTILINE)
    if bullet_matches:
        reasons = []
        seen = set()
        for item in bullet_matches:
            text = clean_text_line(item)
            low = text.lower()
            if len(text) < 20:
                continue
            if any(word in low for word in ["risk remains", "stops need", "capital preservation", "do not initiate", "reduce or exit"]):
                continue
            zh_line = zhify_reason(text)
            key = zh_line.lower()
            if key in seen:
                continue
            seen.add(key)
            reasons.append(zh_line[:120])
            if len(reasons) >= 4:
                return reasons

    lines = split_decision_lines(decision)
    reasons = []
    seen = set()
    preferred_markers = [
        "bullish", "bearish", "rebound", "trend", "momentum", "support", "resistance",
        "sma", "ema", "macd", "rsi", "vwma", "atr", "breakout", "consolidation",
        "长期", "短期", "趋势", "动量", "反弹", "支撑", "阻力", "波动"
    ]
    reject_markers = [
        "close on ", "open on ", "high on ", "low on ", "volume:", "dividends", "stock splits",
        "2024-", "2023-", "2022-"
    ]
    for ln in lines:
        low = ln.lower()
        if len(ln) < 28:
            continue
        if is_mostly_numeric_line(ln):
            continue
        if any(word in low for word in ["risk", "volatile", "uncertain", "caution", "warning", "wait and see", "position sizing", "stop"]):
            continue
        if any(marker in low for marker in reject_markers) and not any(marker in low for marker in preferred_markers):
            continue
        score = 0
        if any(marker in low for marker in preferred_markers):
            score += 2
        if any(ch.isdigit() for ch in ln):
            score += 1
        if score <= 0:
            continue
        zh_line = zhify_reason(ln)
        key = zh_line[:120].lower()
        if key in seen:
            continue
        seen.add(key)
        reasons.append(zh_line[:120])
        if len(reasons) >= 3:
            break
    if not reasons:
        for ln in lines:
            if len(ln) >= 28 and not is_mostly_numeric_line(ln):
                zh_line = zhify_reason(ln)
                key = zh_line[:120].lower()
                if key in seen:
                    continue
                seen.add(key)
                reasons.append(zh_line[:120])
            if len(reasons) >= 3:
                break
    return reasons


def extract_risks(decision: str) -> list[str]:
    core = extract_decision_core(decision)
    bullet_matches = re.findall(r"^\s*[-*]\s+(.+)$", core, flags=re.MULTILINE)
    if bullet_matches:
        risks = []
        seen = set()
        for item in bullet_matches:
            text = clean_text_line(item)
            low = text.lower()
            if len(text) < 20:
                continue
            if not any(word in low for word in ["risk", "below", "weaken", "fading", "volatile", "retest", "downside", "reduce or exit", "do not initiate", "capital preservation"]):
                continue
            zh_line = zhify_reason(text)
            key = zh_line.lower()
            if key in seen:
                continue
            seen.add(key)
            risks.append(zh_line[:120])
            if len(risks) >= 3:
                return risks

    lines = split_decision_lines(decision)
    hits = []
    seen = set()
    hard_risk_markers = [
        "risk", "risks", "volatile", "volatility", "uncertain", "uncertainty", "caution", "warning",
        "wait", "pullback", "breakdown", "lose", "rejection", "stop", "position sizing",
        "回撤", "风险", "波动", "谨慎", "跌破", "失守", "等待", "仓位", "止损"
    ]
    soft_risk_markers = [
        "below the 200-day sma", "below the short-term ema", "below the vwma", "decision point",
        "fading", "losing force", "still bearish", "structurally weak", "retest", "downside"
    ]
    for ln in lines:
        low = ln.lower()
        if len(ln) < 24:
            continue
        if is_mostly_numeric_line(ln):
            continue
        matched = any(word in low for word in hard_risk_markers)
        if not matched and any(word in low for word in soft_risk_markers):
            matched = True
        if not matched:
            continue
        zh_line = zhify_reason(ln)
        key = zh_line[:120].lower()
        if key in seen:
            continue
        seen.add(key)
        hits.append(zh_line[:120])
        if len(hits) >= 3:
            break
    return hits


def archive_outputs(stem: str):
    for src in [STATUS_PATH, RESULT_MD_PATH, RESULT_JSON_PATH, LOG_PATH]:
        if src.exists():
            ext = src.suffix
            dst = HISTORY_DIR / f"{stem}-{src.stem}{ext}"
            shutil.copy2(src, dst)


def build_lightweight_market_fallback(ticker: str, trade_date: str, profile_name: str, language: str, reason: str, duration_ms: int) -> dict | None:
    script = (
        "import json, yfinance as yf; "
        f"df=yf.Ticker('{ticker}').history(period='10d'); "
        "assert not df.empty, 'empty_history'; "
        "close=float(df['Close'].iloc[-1]); "
        "prev=float(df['Close'].iloc[-2]) if len(df)>1 else close; "
        "ma5=float(df['Close'].tail(5).mean()); "
        "chg=(close-prev)/prev*100 if prev else 0.0; "
        "trend='UP' if close>=ma5 else 'DOWN'; "
        "print(json.dumps({'close':close,'prev':prev,'ma5':ma5,'change_pct':chg,'trend':trend}, ensure_ascii=False))"
    )
    try:
        proc = subprocess.run(
            [sys.executable, "-c", script],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=35,
            check=True,
        )
        payload = json.loads((proc.stdout or "").strip())
    except Exception:
        return None

    close = float(payload.get("close"))
    prev = float(payload.get("prev"))
    ma5 = float(payload.get("ma5"))
    change_pct = float(payload.get("change_pct"))
    trend = str(payload.get("trend") or "FLAT")
    if change_pct >= 2:
        decision = "BUY"
    elif change_pct <= -2:
        decision = "SELL"
    else:
        decision = "HOLD"
    trend_zh = "站上5日均线" if trend == "UP" else "回到5日均线下方"
    direction_zh = "上涨" if change_pct >= 0 else "下跌"
    summary_zh = (
        f"深度分析未完成，已自动降级为轻量行情摘要：{ticker} 在 {trade_date} 收盘约 {close:.2f} 美元，"
        f"较前一交易日{direction_zh} {abs(change_pct):.2f}%，当前{trend_zh}。"
    )
    return {
        "ok": True,
        "ticker": ticker,
        "date": trade_date,
        "provider": "yfinance",
        "model": "lightweight-market-fallback",
        "base_url": None,
        "profile": f"{profile_name}_fallback",
        "selected_analysts": ["market"],
        "decision": decision,
        "summary_zh": summary_zh,
        "key_reasons": [
            reason,
            f"最新收盘价 {close:.2f}，前收 {prev:.2f}，单日涨跌幅 {change_pct:+.2f}%",
            f"5日均线约 {ma5:.2f}，当前价格与短线均线关系为：{trend_zh}",
        ],
        "risks": [
            "该结果未包含完整 TradingAgents 多角色深度推理，只适合作为降级版参考",
            "若需要高置信结论，建议后续对白名单个股单独重跑深度分析",
        ],
        "generated_at": utc_now(),
        "duration_ms": duration_ms,
        "retry_count": 0,
        "fallback_used": True,
        "language": language,
        "recovered_from_exception": reason,
    }


def persist_fallback_result(initial_status: dict, fallback_result: dict, step: str, error_type: str, error_message: str):
    result_md = (
        f"# TradingAgents Result\n\n"
        f"## Basic Info\n"
        f"- Ticker: {fallback_result['ticker']}\n"
        f"- Date: {fallback_result['date']}\n"
        f"- Provider: {fallback_result['provider']}\n"
        f"- Model: {fallback_result['model']}\n"
        f"- Profile: {fallback_result['profile']}\n"
        f"- Analysts: {', '.join(fallback_result['selected_analysts'])}\n"
        f"- Duration: {fallback_result['duration_ms']} ms\n\n"
        f"## 中文结论\n\n{zh_decision_label(fallback_result['decision'])}（{fallback_result['decision']}）\n\n"
        f"## 中文摘要\n\n{fallback_result['summary_zh']}\n\n"
        f"## 中文核心依据\n" + "\n".join([f"- {r}" for r in fallback_result['key_reasons']]) + "\n\n"
        f"## 中文主要风险\n" + "\n".join([f"- {r}" for r in fallback_result['risks']]) + "\n"
    )
    RESULT_MD_PATH.write_text(result_md, encoding="utf-8")
    write_json(RESULT_JSON_PATH, fallback_result)
    status = {
        **initial_status,
        "ok": True,
        "provider": fallback_result["provider"],
        "model": fallback_result["model"],
        "base_url": fallback_result.get("base_url"),
        "profile": fallback_result["profile"],
        "selected_analysts": fallback_result["selected_analysts"],
        "step": step,
        "error": error_message,
        "error_type": error_type,
        "duration_ms": fallback_result["duration_ms"],
        "retry_count": fallback_result.get("retry_count", 0),
        "fallback_used": True,
        "language": fallback_result["language"],
        "generated_at": utc_now(),
    }
    write_json(STATUS_PATH, status)


    started = datetime.now()
    profile_order = resolve_profile_list(args.profile)
    last_error = None
    total_retries = 0
    fallback_used = False

    for idx, profile_name in enumerate(profile_order):
        params = resolve_run_params(args, profile_name)
        provider = params["provider"]
        model = params["model"]
        base_url = params["base_url"]
        api_key = params["api_key"]
        selected_analysts = params["analysts"]
        language = params["language"]
def invoke_tradingagents(ticker: str, trade_date: str, provider: str, model: str, base_url: str | None, api_key: str | None, selected_analysts: list[str], api_version: str | None = None, transport: str | None = None):
    sys.path.insert(0, str(REPO_DIR))
    from tradingagents.graph.trading_graph import TradingAgentsGraph
    from tradingagents.default_config import DEFAULT_CONFIG

    if provider == "openai" and api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    if provider == "google" and api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        os.environ["GEMINI_API_KEY"] = api_key
        if api_version:
            os.environ["GOOGLE_API_VERSION"] = api_version
            os.environ["GEMINI_API_VERSION"] = api_version

    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = provider
    if base_url:
        config["backend_url"] = base_url
    config["deep_think_llm"] = model
    config["quick_think_llm"] = model
    config["max_debate_rounds"] = 1
    config["max_risk_discuss_rounds"] = 1
    config["data_vendors"] = {
        "core_stock_apis": "yfinance",
        "technical_indicators": "yfinance",
        "fundamental_data": "yfinance",
        "news_data": "yfinance",
    }
    if provider == "google":
        config["google_api_version"] = api_version or "v1beta"
        config["google_transport"] = transport or "rest"
    ta = TradingAgentsGraph(selected_analysts=selected_analysts, debug=True, config=config)
    return ta.propagate(ticker, trade_date)


def run_bridge(args, initial_status: dict):
    started = datetime.now()
    profile_order = resolve_profile_list(args.profile)
    last_error = None
    total_retries = 0
    fallback_used = False

    for idx, profile_name in enumerate(profile_order):
        params = resolve_run_params(args, profile_name)
        provider = params["provider"]
        model = params["model"]
        base_url = params["base_url"]
        api_key = params["api_key"]
        selected_analysts = params["analysts"]
        language = params["language"]
        retry_count = params["retry_count"]
        retry_wait_seconds = params["retry_wait_seconds"]
        if idx > 0:
            fallback_used = True

        print(f"BRIDGE_START ticker={args.ticker} date={args.date} provider={provider} model={model} analysts={selected_analysts} profile={profile_name}")
        running_status = {
            **initial_status,
            "provider": provider,
            "model": model,
            "base_url": base_url,
            "profile": profile_name,
            "selected_analysts": selected_analysts,
            "step": "running",
            "retry_count": total_retries,
            "fallback_used": fallback_used,
            "language": language,
            "generated_at": utc_now(),
        }
        write_json(STATUS_PATH, running_status)
        for attempt in range(retry_count + 1):
            try:
                state, decision = invoke_tradingagents(
                    args.ticker,
                    args.date,
                    provider,
                    model,
                    base_url,
                    api_key,
                    selected_analysts,
                    api_version=params.get("api_version"),
                    transport=params.get("transport"),
                )
                decision_text = decision if isinstance(decision, str) else str(decision)
                extraction_source = decision_text
                try:
                    if LOG_PATH.exists():
                        log_text = LOG_PATH.read_text(encoding="utf-8", errors="replace")
                        if "FINAL TRANSACTION PROPOSAL" in log_text.upper():
                            extraction_source = log_text
                except Exception:
                    pass
                normalized_decision = normalize_decision_label(extraction_source)
                key_reasons = ensure_chinese_bullets(extract_key_reasons(extraction_source), "reason")
                risks = ensure_chinese_bullets(extract_risks(extraction_source), "risk")
                summary_zh = summarize_zh(extraction_source, args.ticker, args.date, provider, model, selected_analysts, key_reasons, risks)
                duration_ms = int((datetime.now() - started).total_seconds() * 1000)
                result_md = (
                    f"# TradingAgents Result\n\n"
                    f"## Basic Info\n"
                    f"- Ticker: {args.ticker}\n"
                    f"- Date: {args.date}\n"
                    f"- Provider: {provider}\n"
                    f"- Model: {model}\n"
                    f"- Profile: {profile_name}\n"
                    f"- Analysts: {', '.join(selected_analysts)}\n"
                    f"- Duration: {duration_ms} ms\n\n"
                    f"## Final Decision\n\n{decision_text}\n\n"
                    f"## 中文结论\n\n{zh_decision_label(normalized_decision)}（{normalized_decision}）\n\n"
                    f"## 中文摘要\n\n{summary_zh}\n\n"
                    f"## 中文核心依据\n" + ("\n".join([f"- {r}" for r in key_reasons]) if key_reasons else "- 暂未稳定提炼到中文依据") + "\n\n"
                    f"## 中文主要风险\n" + ("\n".join([f"- {r}" for r in risks]) if risks else "- 暂未稳定提炼到中文风险") + "\n"
                )
                RESULT_MD_PATH.write_text(result_md, encoding="utf-8")
                result_json = {
                    "ok": True,
                    "ticker": args.ticker,
                    "date": args.date,
                    "provider": provider,
                    "model": model,
                    "base_url": base_url,
                    "profile": profile_name,
                    "selected_analysts": selected_analysts,
                    "decision": normalized_decision,
                    "summary_zh": summary_zh,
                    "key_reasons": key_reasons,
                    "risks": risks,
                    "state_keys": list(state.keys()) if isinstance(state, dict) else None,
                    "generated_at": utc_now(),
                    "duration_ms": duration_ms,
                    "retry_count": total_retries,
                    "fallback_used": fallback_used,
                    "language": language,
                }
                write_json(RESULT_JSON_PATH, result_json)
                status = {
                    **initial_status,
                    "ok": True,
                    "provider": provider,
                    "model": model,
                    "base_url": base_url,
                    "profile": profile_name,
                    "selected_analysts": selected_analysts,
                    "step": "completed",
                    "error": None,
                    "error_type": None,
                    "duration_ms": duration_ms,
                    "retry_count": total_retries,
                    "fallback_used": fallback_used,
                    "language": language,
                    "generated_at": utc_now(),
                }
                write_json(STATUS_PATH, status)
                if params["save_history"]:
                    archive_outputs(ts_slug())
                print(f"BRIDGE_OK ticker={args.ticker} date={args.date} provider={provider} model={model} profile={profile_name}")
                return 0
            except Exception as e:
                tb = traceback.format_exc()
                err_text = f"{e}\n{tb}"
                try:
                    log_text = LOG_PATH.read_text(encoding="utf-8", errors="replace") if LOG_PATH.exists() else ""
                except Exception:
                    log_text = ""
                if "FINAL TRANSACTION PROPOSAL" in log_text.upper():
                    extraction_source = log_text
                    normalized_decision = normalize_decision_label(extraction_source)
                    key_reasons = ensure_chinese_bullets(extract_key_reasons(extraction_source), "reason")
                    risks = ensure_chinese_bullets(extract_risks(extraction_source), "risk")
                    summary_zh = summarize_zh(extraction_source, args.ticker, args.date, provider, model, selected_analysts, key_reasons, risks)
                    duration_ms = int((datetime.now() - started).total_seconds() * 1000)
                    result_md = (
                        f"# TradingAgents Result\n\n"
                        f"## Basic Info\n"
                        f"- Ticker: {args.ticker}\n"
                        f"- Date: {args.date}\n"
                        f"- Provider: {provider}\n"
                        f"- Model: {model}\n"
                        f"- Profile: {profile_name}\n"
                        f"- Analysts: {', '.join(selected_analysts)}\n"
                        f"- Duration: {duration_ms} ms\n\n"
                        f"## Final Decision\n\n{extract_decision_core(extraction_source)}\n\n"
                        f"## 中文结论\n\n{zh_decision_label(normalized_decision)}（{normalized_decision}）\n\n"
                        f"## 中文摘要\n\n{summary_zh}\n\n"
                        f"## 中文核心依据\n" + ("\n".join([f"- {r}" for r in key_reasons]) if key_reasons else "- 暂未稳定提炼到中文依据") + "\n\n"
                        f"## 中文主要风险\n" + ("\n".join([f"- {r}" for r in risks]) if risks else "- 暂未稳定提炼到中文风险") + "\n"
                    )
                    RESULT_MD_PATH.write_text(result_md, encoding="utf-8")
                    result_json = {
                        "ok": True,
                        "ticker": args.ticker,
                        "date": args.date,
                        "provider": provider,
                        "model": model,
                        "base_url": base_url,
                        "profile": profile_name,
                        "selected_analysts": selected_analysts,
                        "decision": normalized_decision,
                        "summary_zh": summary_zh,
                        "key_reasons": key_reasons,
                        "risks": risks,
                        "state_keys": None,
                        "generated_at": utc_now(),
                        "duration_ms": duration_ms,
                        "retry_count": total_retries,
                        "fallback_used": fallback_used,
                        "language": language,
                        "recovered_from_exception": str(e),
                    }
                    write_json(RESULT_JSON_PATH, result_json)
                    status = {
                        **initial_status,
                        "ok": True,
                        "provider": provider,
                        "model": model,
                        "base_url": base_url,
                        "profile": profile_name,
                        "selected_analysts": selected_analysts,
                        "step": "completed_with_recovery",
                        "error": str(e),
                        "error_type": classify_error(err_text),
                        "duration_ms": duration_ms,
                        "retry_count": total_retries,
                        "fallback_used": fallback_used,
                        "language": language,
                        "generated_at": utc_now(),
                    }
                    write_json(STATUS_PATH, status)
                    if params["save_history"]:
                        archive_outputs(ts_slug())
                    print(f"BRIDGE_OK_RECOVERED ticker={args.ticker} date={args.date} provider={provider} model={model} profile={profile_name}")
                    return 0
                error_type = classify_error(err_text)
                duration_ms = int((datetime.now() - started).total_seconds() * 1000)
                if error_type == "timeout_error":
                    fallback_result = build_lightweight_market_fallback(
                        args.ticker,
                        args.date,
                        profile_name,
                        language,
                        f"单票深度分析超时，已自动降级为轻量行情结论（provider={provider}, model={model}）",
                        duration_ms,
                    )
                    if fallback_result:
                        fallback_result["retry_count"] = total_retries
                        persist_fallback_result(initial_status, fallback_result, "completed_with_timeout_fallback", error_type, str(e))
                        if params["save_history"]:
                            archive_outputs(ts_slug())
                        print(f"BRIDGE_OK_TIMEOUT_FALLBACK ticker={args.ticker} date={args.date} provider={provider} model={model} profile={profile_name}")
                        return 0
                last_error = (str(e), error_type, profile_name)
                if should_retry(error_type) and attempt < retry_count:
                    total_retries += 1
                    print(f"BRIDGE_RETRY error_type={error_type} wait={retry_wait_seconds}s attempt={attempt+1}")
                    time.sleep(retry_wait_seconds)
                    continue
                break

    duration_ms = int((datetime.now() - started).total_seconds() * 1000)
    error_message, error_type, profile_name = last_error if last_error else ("unknown error", "runtime_error", None)
    fail_status = {
        **initial_status,
        "ok": False,
        "step": "bridge_runtime",
        "error_type": error_type,
        "error": error_message,
        "generated_at": utc_now(),
        "duration_ms": duration_ms,
        "retry_count": total_retries,
        "fallback_used": fallback_used,
        "profile": profile_name,
    }
    write_json(STATUS_PATH, fail_status)
    RESULT_MD_PATH.write_text(f"# TradingAgents Bridge Failure\n\n- Error Type: {error_type}\n- Error: {error_message}\n", encoding="utf-8")
    write_json(RESULT_JSON_PATH, fail_status)
    print(f"BRIDGE_FAIL step=bridge_runtime error_type={error_type} error={error_message}")
    return 1


def main():
    parser = argparse.ArgumentParser(description="Run TradingAgents bridge for OpenClaw")
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--profile")
    parser.add_argument("--provider")
    parser.add_argument("--model")
    parser.add_argument("--base-url")
    parser.add_argument("--api-key")
    parser.add_argument("--analysts")
    parser.add_argument("--language", default="zh-CN")
    parser.add_argument("--retry-count", dest="retry_count", type=int)
    parser.add_argument("--retry-wait-seconds", dest="retry_wait_seconds", type=int)
    parser.add_argument("--save-history", dest="save_history", action="store_true")
    parser.add_argument("--no-save-history", dest="save_history", action="store_false")
    parser.set_defaults(save_history=None)
    args = parser.parse_args()

    initial_status = {
        "ok": False,
        "ticker": args.ticker,
        "date": args.date,
        "provider": args.provider,
        "model": args.model,
        "base_url": args.base_url,
        "profile": args.profile,
        "selected_analysts": [a.strip() for a in args.analysts.split(",") if a.strip()] if args.analysts else None,
        "output_md": str(RESULT_MD_PATH),
        "output_json": str(RESULT_JSON_PATH),
        "log_path": str(LOG_PATH),
        "error": None,
        "generated_at": utc_now(),
        "step": "starting",
        "duration_ms": None,
        "retry_count": 0,
        "fallback_used": False,
        "language": args.language,
    }
    write_json(STATUS_PATH, initial_status)

    with LOG_PATH.open("w", encoding="utf-8") as log_fp, redirect_stdout(log_fp), redirect_stderr(log_fp):
        try:
            return run_bridge(args, initial_status)
        except Exception as e:
            tb = traceback.format_exc()
            err_text = f"{e}\n{tb}"
            error_type = classify_error(err_text)
            fail_status = {
                **initial_status,
                "ok": False,
                "step": "bridge_runtime",
                "error_type": error_type,
                "error": str(e),
                "generated_at": utc_now(),
            }
            write_json(STATUS_PATH, fail_status)
            RESULT_MD_PATH.write_text(f"# TradingAgents Bridge Failure\n\n- Error Type: {error_type}\n- Error: {e}\n", encoding="utf-8")
            write_json(RESULT_JSON_PATH, fail_status)
            print(f"BRIDGE_FAIL step=bridge_runtime error_type={error_type} error={e}")
            print(tb)
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
