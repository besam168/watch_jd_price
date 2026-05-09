import argparse
import ctypes
import ctypes.wintypes
import json
import re
import smtplib
import sys
import time
import webbrowser
from dataclasses import asdict, dataclass, field
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from PIL import Image, ImageEnhance, ImageFilter, ImageGrab, ImageOps
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = DATA_DIR / "config.json"
STATE_PATH = DATA_DIR / "state_multi.json"
LOG_PATH = DATA_DIR / "price_log.jsonl"
SCREENSHOT_PATH = BASE_DIR / "latest_page.png"
OCR_INPUT_PATH = BASE_DIR / "active_window_price.png"
OCR_AUTO_SCREENSHOT_PATH = BASE_DIR / "active_window_auto.png"
OCR_DEBUG_DIR = BASE_DIR / "ocr_debug"
OCR_DEBUG_DIR.mkdir(parents=True, exist_ok=True)

CHROME_PROFILE = Path.home() / 'AppData/Local/Google/Chrome/User Data'
EDGE_PROFILE = Path.home() / 'AppData/Local/Microsoft/Edge/User Data'
TESSERACT_PATH = Path(r'C:\Program Files\Tesseract-OCR\tesseract.exe')


def list_profile_dirs(root: Path) -> List[Path]:
    if not root.exists():
        return []
    names = [
        'Default',
        'Profile 1', 'Profile 2', 'Profile 3', 'Profile 4', 'Profile 5',
        'Guest Profile', 'System Profile'
    ]
    found: List[Path] = []
    for name in names:
        p = root / name
        if p.exists() and p.is_dir():
            found.append(p)
    return found


DEFAULT_CONFIG = {
    "product_name": "京东 iPhone 17 256G",
    "product_url": "https://item.jd.com/100278222276.html",
    "allowed_store_keywords": ["自营", "旗舰店", "Apple"],
    "poll_minutes": 30,
    "baseline_price": 5590.0,
    "price_min": 4000.0,
    "price_max": 9000.0,
    "max_rise_pct_from_baseline": 0.25,
    "known_bad_prices": [11000.0, 11041.0, 2019.0, 2022.0, 1800.0],
    "only_notify_below_baseline": True,
    "notify_on_any_drop": True,
    "notify_min_drop": 1.0,
    "suppress_first_record_notice": True,
    "qq_email_to": "758622673@qq.com",
    "smtp": {
        "host": "smtp.qq.com",
        "port": 465,
        "user": "910633260@qq.com",
        "password": "sghqeeeeyuzjbcbb"
    }
}


@dataclass
class ExtractAttempt:
    name: str
    ok: bool
    price: Optional[float] = None
    price_text: str = ""
    title: str = ""
    store_text: str = ""
    raw_hint: str = ""
    error: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Snapshot:
    title: str
    price: Optional[float]
    store_text: str
    in_stock: Optional[bool]
    url: str
    fetched_at: str
    extractor: str
    raw_hint: str = ""
    attempts: List[Dict[str, Any]] = field(default_factory=list)


def ensure_config() -> Dict[str, Any]:
    changed = False
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2), encoding="utf-8")
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    for key, value in DEFAULT_CONFIG.items():
        if key not in cfg:
            cfg[key] = value
            changed = True
    if cfg.get("product_url") != DEFAULT_CONFIG["product_url"]:
        cfg["product_url"] = DEFAULT_CONFIG["product_url"]
        changed = True
    if changed:
        CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return cfg


def load_state() -> Dict[str, Any]:
    if not STATE_PATH.exists():
        return {}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: Dict[str, Any]) -> None:
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def append_log(snapshot: Snapshot) -> None:
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(snapshot), ensure_ascii=False) + "\n")


def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return r.text


def extract_title(html: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    if not m:
        return "未知商品"
    return re.sub(r"\s+", " ", m.group(1)).strip()


def extract_price_candidates(text: str) -> List[float]:
    hits: List[float] = []
    patterns = [
        r'"price"\s*:\s*"([0-9]+(?:\.[0-9]+)?)"',
        r'price[:=]\s*"?([0-9]+(?:\.[0-9]+)?)"?',
        r'jdPrice[:=]\s*"?([0-9]+(?:\.[0-9]+)?)"?',
        r'[¥￥]\s*([0-9]{3,5}(?:\.[0-9]{1,2})?)',
        r'([0-9]{4,5}(?:\.[0-9]{1,2})?)',
    ]
    for p in patterns:
        for m in re.finditer(p, text, re.I):
            try:
                val = float(m.group(1))
            except ValueError:
                continue
            if 1000 <= val <= 20000 and val not in hits:
                hits.append(val)
    return hits


def score_price_candidates(text: str, values: List[float]) -> List[Tuple[float, float, str]]:
    ranked: List[Tuple[float, float, str]] = []
    lowered = text.lower()
    for val in values:
        score = 0.0
        reason: List[str] = []
        s1 = f"{int(val)}"
        s2 = f"{val:.2f}"
        idx = text.find(s2)
        if idx < 0:
            idx = text.find(s1)
        window = text[max(0, idx - 120): idx + 120] if idx >= 0 else ""
        window_lower = window.lower()

        if 3000 <= val <= 12000:
            score += 3.0
            reason.append('range_ok')
        elif 2000 <= val < 3000:
            score -= 2.5
            reason.append('too_low')
        elif val > 15000:
            score -= 4.0
            reason.append('too_high')

        if any(k in window for k in ['京东价', '到手价', '活动价', '抢购价']):
            score += 4.0
            reason.append('near_price_label')
        if any(k in window for k in ['￥', '¥']):
            score += 2.5
            reason.append('near_currency')
        if 'iphone 17' in lowered and idx >= 0 and 'iphone 17' in window_lower:
            score += 1.5
            reason.append('near_product_name')
        if any(k in window for k in ['促销', '满减', '优惠券', 'PLUS', '赠品']):
            score -= 1.5
            reason.append('promo_noise')
        if any(k in window_lower for k in ['评论', '好评', '销量', '排行', '关注']):
            score -= 2.0
            reason.append('non_price_metric')
        if val in (1800.0, 2019.0, 11000.0):
            score -= 1.0
            reason.append('known_suspicious_seen_value')
        ranked.append((val, score, ','.join(reason)))
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked


def pick_best_price(values: List[float], context_text: str = "") -> Optional[float]:
    if not values:
        return None
    ranked = score_price_candidates(context_text or "", values)
    return ranked[0][0] if ranked and ranked[0][1] > -1.5 else values[0]


def nearly_same_price(a: float, b: float, tolerance: float = 0.01) -> bool:
    return abs(float(a) - float(b)) <= tolerance


def valid_watch_price(price: Optional[float], config: Dict[str, Any]) -> Tuple[bool, str]:
    if price is None:
        return False, "missing_price"
    price = float(price)
    baseline = float(config.get("baseline_price") or 0)
    min_price = float(config.get("price_min") or 0)
    max_price = float(config.get("price_max") or 999999)
    known_bad = [float(x) for x in config.get("known_bad_prices", [])]
    if any(nearly_same_price(price, bad) for bad in known_bad):
        return False, "known_bad_price"
    if price < min_price:
        return False, "below_watch_range"
    if price > max_price:
        return False, "above_watch_range"
    if baseline > 0:
        max_rise_pct = float(config.get("max_rise_pct_from_baseline", 0.25))
        if price > baseline * (1 + max_rise_pct):
            return False, "too_far_above_baseline"
    return True, "valid"


def sanitize_attempt_price(attempt: ExtractAttempt, config: Dict[str, Any]) -> ExtractAttempt:
    ok, reason = valid_watch_price(attempt.price, config)
    if ok or attempt.price is None:
        return attempt
    attempt.meta["rejected_price"] = attempt.price
    attempt.meta["reject_reason"] = reason
    attempt.price = None
    return attempt


def attempt_priority(name: str) -> int:
    priorities = {
        "active_window_ocr": 90,
        "real_session_probe": 80,
        "playwright_dom": 70,
        "profile_scan": 60,
        "requests_with_profile_cookies": 50,
        "script_json": 30,
        "requests_html": 20,
    }
    return priorities.get(name, 10)


def extract_json_from_scripts(html: str) -> List[float]:
    hits: List[float] = []
    script_bodies = re.findall(r"<script[^>]*>(.*?)</script>", html, re.I | re.S)
    for body in script_bodies:
        body_lower = body.lower()
        if not any(k in body_lower for k in ["price", "jdprice", "sku", "100278222276"]):
            continue
        for val in extract_price_candidates(body):
            if val not in hits:
                hits.append(val)
    return hits


def extract_store_text(html: str) -> str:
    for keyword in ["Apple产品京东自营旗舰店", "自营", "旗舰店", "Apple", "京东"]:
        idx = html.find(keyword)
        if idx >= 0:
            snippet = html[max(0, idx - 80): idx + 160]
            snippet = re.sub(r"<[^>]+>", " ", snippet)
            snippet = re.sub(r"\s+", " ", snippet).strip()
            return snippet[:160]
    return ""


def load_cookie_header(profile_dir: Path) -> str:
    cookie_path = profile_dir / 'Network' / 'Cookies'
    if not cookie_path.exists():
        return ''
    try:
        import sqlite3
        conn = sqlite3.connect(str(cookie_path))
        cur = conn.cursor()
        cur.execute(
            "SELECT name, value FROM cookies WHERE host_key LIKE ? OR host_key LIKE ?",
            ('%jd.com', '%3.cn')
        )
        rows = cur.fetchall()
        conn.close()
        parts = []
        for name, value in rows:
            if name and value:
                parts.append(f'{name}={value}')
        return '; '.join(parts)
    except Exception:
        return ''


def infer_stock(text: str) -> Optional[bool]:
    if "无货" in text:
        return False
    if any(x in text for x in ["有货", "现货", "立即购买", "加入购物车"]):
        return True
    return None


def attempt_requests_html(url: str) -> ExtractAttempt:
    try:
        html = fetch_html(url)
        title = extract_title(html)
        price_values = extract_price_candidates(html)
        price = pick_best_price(price_values, html)
        store_text = extract_store_text(html)
        return ExtractAttempt(
            name="requests_html",
            ok=True,
            price=price,
            title=title,
            store_text=store_text,
            raw_hint=f"html_prices={price_values[:10]}; ranked={score_price_candidates(html, price_values)[:5]}; store={store_text}"
        )
    except Exception as e:
        return ExtractAttempt(name="requests_html", ok=False, error=str(e))


def attempt_requests_with_profile_cookies(url: str) -> ExtractAttempt:
    profile = pick_profile()
    if profile is None:
        return ExtractAttempt(name='requests_with_profile_cookies', ok=False, error='No browser profile found')
    cookie_header = load_cookie_header(profile)
    if not cookie_header:
        return ExtractAttempt(name='requests_with_profile_cookies', ok=False, error='No JD cookies found in profile')
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cookie': cookie_header,
            'Referer': url,
        }
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        html = r.text
        title = extract_title(html)
        values = extract_price_candidates(html) + extract_json_from_scripts(html)
        price = pick_best_price(values, html)
        store_text = extract_store_text(html)
        logged_words = any(x in html for x in ['退出登录', '我的京东', '欢迎您'])
        return ExtractAttempt(
            name='requests_with_profile_cookies',
            ok=True,
            price=price,
            title=title,
            store_text=store_text,
            raw_hint=f'logged_words={logged_words}; cookie_len={len(cookie_header)}; values={values[:10]}',
            meta={'profile_dir': str(profile), 'logged_words': logged_words, 'cookie_len': len(cookie_header)}
        )
    except Exception as e:
        return ExtractAttempt(name='requests_with_profile_cookies', ok=False, error=str(e))


def attempt_script_json(url: str) -> ExtractAttempt:
    try:
        html = fetch_html(url)
        title = extract_title(html)
        values = extract_json_from_scripts(html)
        price = pick_best_price(values, html)
        store_text = extract_store_text(html)
        return ExtractAttempt(
            name="script_json",
            ok=True,
            price=price,
            title=title,
            store_text=store_text,
            raw_hint=f"script_prices={values[:10]}; store={store_text}"
        )
    except Exception as e:
        return ExtractAttempt(name="script_json", ok=False, error=str(e))


def pick_profile() -> Optional[Path]:
    profiles = list_profile_dirs(CHROME_PROFILE)
    if profiles:
        return profiles[0]
    profiles = list_profile_dirs(EDGE_PROFILE)
    if profiles:
        return profiles[0]
    return None


def browser_root_for_profile(profile_dir: Path) -> Path:
    return profile_dir.parent


def profile_name(profile_dir: Path) -> str:
    return profile_dir.name


def attempt_playwright_dom(url: str) -> ExtractAttempt:
    profile = pick_profile()
    if profile is None:
        return ExtractAttempt(name="playwright_dom", ok=False, error="No browser profile found")
    try:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(browser_root_for_profile(profile)),
                headless=True,
                args=[f'--profile-directory={profile_name(profile)}'],
                viewport={'width': 1440, 'height': 2400},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36',
            )
            page = context.new_page()
            page.goto(url, wait_until='networkidle', timeout=90000)
            page.wait_for_timeout(12000)
            title = page.title()
            body = page.locator('body').inner_text(timeout=10000)
            store = ''
            for sel in ['text=Apple产品京东自营旗舰店', '.itemover-tip', '.p-parameter .parameter2']:
                try:
                    store = page.locator(sel).first.inner_text(timeout=2000).strip()
                    if store:
                        break
                except Exception:
                    pass
            price_parts = []
            selectors_snapshot: Dict[str, str] = {}
            for sel in ['.price.J-p-100278222276', '.p-price .price', '.dd .p-price']:
                try:
                    txt = page.locator(sel).first.inner_text(timeout=3000).strip()
                    selectors_snapshot[sel] = txt
                    if txt:
                        price_parts.append(f'{sel}={txt}')
                except Exception as e:
                    selectors_snapshot[sel] = f'<ERR:{e}>'
            page.screenshot(path=str(SCREENSHOT_PATH), full_page=True)
            is_login_page = '登录' in body and '免费注册' in body
            has_login_words = any(x in body for x in ['你好，请登录', '免费注册', '京东账号登录'])
            context.close()
        price_text = ' | '.join(price_parts)
        price = pick_best_price(extract_price_candidates(price_text + "\n" + body[:5000]), body)
        return ExtractAttempt(
            name="playwright_dom",
            ok=True,
            price=price,
            price_text=price_text,
            title=title,
            store_text=store,
            raw_hint=(body[:800].replace("\n", " ") if body else ""),
            meta={
                "profile_dir": str(profile),
                "is_login_page": is_login_page,
                "has_login_words": has_login_words,
                "selectors_snapshot": selectors_snapshot,
                "body_snip": body[:1200],
            }
        )
    except Exception as e:
        return ExtractAttempt(name="playwright_dom", ok=False, error=str(e))


def attempt_profile_scan(url: str) -> ExtractAttempt:
    profile_dirs = list_profile_dirs(CHROME_PROFILE) or list_profile_dirs(EDGE_PROFILE)
    if not profile_dirs:
        return ExtractAttempt(name="profile_scan", ok=False, error="No browser profiles found")
    rows: List[Dict[str, Any]] = []
    best_price: Optional[float] = None
    best_title = ""
    best_store = ""
    best_price_text = ""
    for profile in profile_dirs[:6]:
        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(browser_root_for_profile(profile)),
                    headless=True,
                    args=[f'--profile-directory={profile_name(profile)}'],
                    viewport={'width': 1280, 'height': 1600},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36',
                )
                page = context.new_page()
                page.goto(url, wait_until='domcontentloaded', timeout=60000)
                page.wait_for_timeout(8000)
                body = page.locator('body').inner_text(timeout=10000)
                title = page.title()
                price_text = ''
                for sel in ['.price.J-p-100278222276', '.p-price .price', '.dd .p-price']:
                    try:
                        txt = page.locator(sel).first.inner_text(timeout=2000).strip()
                        if txt:
                            price_text += f'{sel}={txt} | '
                    except Exception:
                        pass
                price = pick_best_price(extract_price_candidates(price_text + "\n" + body[:5000]), body)
                row = {
                    'profile': profile.name,
                    'price': price,
                    'price_text': price_text.strip(' |'),
                    'has_login_words': any(x in body for x in ['你好，请登录', '免费注册', '京东账号登录']),
                    'has_store': 'Apple产品京东自营旗舰店' in body,
                    'title': title,
                }
                rows.append(row)
                context.close()
                if best_price is None and price is not None:
                    best_price = price
                    best_title = title
                    best_price_text = price_text.strip(' |')
        except Exception as e:
            rows.append({'profile': profile.name, 'error': str(e)[:300]})
    return ExtractAttempt(
        name='profile_scan',
        ok=True,
        price=best_price,
        price_text=best_price_text,
        title=best_title,
        store_text=best_store,
        raw_hint=f'profile_scan_rows={len(rows)}',
        meta={'rows': rows}
    )


def attempt_real_session_probe(url: str) -> ExtractAttempt:
    profile = pick_profile()
    if profile is None:
        return ExtractAttempt(name="real_session_probe", ok=False, error="No browser profile found")
    try:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(browser_root_for_profile(profile)),
                headless=False,
                channel='chrome' if CHROME_PROFILE.exists() else None,
                args=[f'--profile-directory={profile_name(profile)}'],
                viewport={'width': 1440, 'height': 1600},
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(url, wait_until='domcontentloaded', timeout=90000)
            page.wait_for_timeout(15000)
            title = page.title()
            body = page.locator('body').inner_text(timeout=10000)
            selectors_snapshot: Dict[str, str] = {}
            price_parts = []
            for sel in ['.price.J-p-100278222276', '.p-price .price', '.dd .p-price']:
                try:
                    txt = page.locator(sel).first.inner_text(timeout=3000).strip()
                    selectors_snapshot[sel] = txt
                    if txt:
                        price_parts.append(f'{sel}={txt}')
                except Exception as e:
                    selectors_snapshot[sel] = f'<ERR:{e}>'
            page.screenshot(path=str(BASE_DIR / 'latest_page_real_session.png'), full_page=True)
            context.close()
        price_text = ' | '.join(price_parts)
        price = pick_best_price(extract_price_candidates(price_text + "\n" + body[:5000]), body)
        return ExtractAttempt(
            name="real_session_probe",
            ok=True,
            price=price,
            price_text=price_text,
            title=title,
            raw_hint=body[:800].replace("\n", " "),
            meta={
                "has_login_words": any(x in body for x in ['你好，请登录', '免费注册', '京东账号登录']),
                "selectors_snapshot": selectors_snapshot,
                "body_snip": body[:1200],
            }
        )
    except Exception as e:
        return ExtractAttempt(name="real_session_probe", ok=False, error=str(e))


def get_foreground_window_info() -> Dict[str, Any]:
    """Return foreground window title/rect on Windows; empty dict on failure."""
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return {}
        length = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return {
            'hwnd': int(hwnd),
            'title': buf.value,
            'rect': (int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)),
        }
    except Exception as e:
        return {'error': str(e)}


def get_visible_window_text(user32: Any, hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ''
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value or ''


def enumerate_visible_windows() -> List[Dict[str, Any]]:
    windows: List[Dict[str, Any]] = []
    try:
        user32 = ctypes.windll.user32
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)

        def callback(hwnd: int, lparam: int) -> bool:
            try:
                if not user32.IsWindowVisible(hwnd):
                    return True
                title = get_visible_window_text(user32, hwnd)
                if not title.strip():
                    return True
                rect = ctypes.wintypes.RECT()
                if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                    return True
                left, top, right, bottom = int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)
                width = right - left
                height = bottom - top
                if width < 200 or height < 120:
                    return True
                placement = ctypes.wintypes.UINT()
                windows.append({
                    'hwnd': int(hwnd),
                    'title': title,
                    'rect': (left, top, right, bottom),
                    'width': width,
                    'height': height,
                })
            except Exception:
                return True
            return True

        user32.EnumWindows(EnumWindowsProc(callback), 0)
    except Exception:
        return windows
    return windows


def is_trusted_jd_window(title: str) -> bool:
    title_lower = (title or '').lower()
    trusted_words = ['京东', 'jd.com', 'item.jd.com', 'iphone 17', 'apple', '100278222276']
    blocked_words = ['openclaw', 'tanzo', 'visual studio code', 'cmd.exe', 'powershell']
    if any(x in title_lower for x in blocked_words):
        return False
    return any(x.lower() in title_lower for x in trusted_words)


def score_jd_window(info: Dict[str, Any]) -> Tuple[int, List[str]]:
    title = str(info.get('title', ''))
    title_lower = title.lower()
    score = 0
    reasons: List[str] = []
    if '京东' in title or 'jd.com' in title_lower or 'item.jd.com' in title_lower:
        score += 6
        reasons.append('jd_title')
    if 'iphone 17' in title_lower:
        score += 5
        reasons.append('iphone17')
    if 'apple' in title_lower:
        score += 3
        reasons.append('apple')
    if '100278222276' in title:
        score += 6
        reasons.append('sku')
    if '- google chrome' in title_lower or '- microsoft edge' in title_lower:
        score += 2
        reasons.append('browser')
    width = int(info.get('width', 0) or 0)
    height = int(info.get('height', 0) or 0)
    area = width * height
    if area >= 900000:
        score += 1
        reasons.append('large_area')
    blocked_markers = [
        'openclaw', 'tanzo', 'visual studio code', 'cmd.exe', 'powershell', 'wsws168',
        '设置', 'windows 输入体验', 'program manager', '任务切换', '开始', '搜索'
    ]
    if any(x in title_lower for x in blocked_markers):
        score -= 20
        reasons.append('blocked_title')
    return score, reasons


def pick_best_jd_window() -> Dict[str, Any]:
    foreground = get_foreground_window_info()
    candidates = enumerate_visible_windows()
    ranked: List[Tuple[int, Dict[str, Any], List[str]]] = []
    for info in candidates:
        score, reasons = score_jd_window(info)
        if score > 0:
            ranked.append((score, info, reasons))
    ranked.sort(key=lambda x: x[0], reverse=True)

    if ranked:
        best_score, best_info, reasons = ranked[0]
        best = dict(best_info)
        best['trusted_jd_window'] = is_trusted_jd_window(str(best.get('title', '')))
        best['selection'] = 'enumerated_best_match'
        best['selection_score'] = best_score
        best['selection_reasons'] = reasons
        best['foreground_title'] = str(foreground.get('title', '')) if foreground else ''
        best['candidate_count'] = len(ranked)
        best['top_candidates'] = [
            {
                'title': item[1].get('title', ''),
                'rect': item[1].get('rect'),
                'score': item[0],
                'reasons': item[2],
            }
            for item in ranked[:5]
        ]
        if best['trusted_jd_window']:
            return best

    if foreground:
        info = dict(foreground)
        info['trusted_jd_window'] = is_trusted_jd_window(str(info.get('title', '')))
        info['selection'] = 'foreground_fallback'
        info['candidate_count'] = len(ranked)
        info['top_candidates'] = [
            {
                'title': item[1].get('title', ''),
                'rect': item[1].get('rect'),
                'score': item[0],
                'reasons': item[2],
            }
            for item in ranked[:5]
        ]
        return info
    return {}


def capture_foreground_window(output_path: Path = OCR_AUTO_SCREENSHOT_PATH) -> Tuple[Optional[Path], Dict[str, Any]]:
    """Capture the best JD-like browser window on Windows; fallback to foreground/fullscreen."""
    info = pick_best_jd_window()
    try:
        bbox = info.get('rect') if info else None
        if bbox:
            left, top, right, bottom = bbox
            if right > left and bottom > top:
                img = ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
            else:
                img = ImageGrab.grab(all_screens=True)
                info['fallback'] = 'invalid_window_rect_fullscreen'
        else:
            img = ImageGrab.grab(all_screens=True)
            info['fallback'] = 'no_window_rect_fullscreen'
        img.save(output_path)
        info['screenshot_path'] = str(output_path)
        info['screenshot_size'] = img.size
        return output_path, info
    except Exception as e:
        info['capture_error'] = str(e)
        return None, info


def normalize_ocr_text(text: str) -> str:
    text = text.replace(',', '').replace('，', '')
    text = text.replace('¥', '￥').replace('Y', '￥').replace('y', '￥')
    text = text.replace('O', '0').replace('o', '0').replace('I', '1').replace('l', '1')
    # Join OCR-spaced 4-5 digit prices such as "5 5 9 0".
    text = re.sub(r'(?<!\d)((?:\d\s+){3,4}\d)(?!\d)', lambda m: m.group(1).replace(' ', ''), text)
    return text


def extract_ocr_price_candidates(text: str) -> List[float]:
    normalized = normalize_ocr_text(text)
    hits: List[float] = []

    patterns = [
        r'￥\s*([0-9]{3,5}(?:\.[0-9]{1,2})?)',
        r'(?<!\d)([0-9]{4,5}(?:\.[0-9]{1,2})?)(?!\d)',
    ]
    for pattern in patterns:
        for m in re.finditer(pattern, normalized):
            try:
                val = float(m.group(1))
            except ValueError:
                continue
            if 1000 <= val <= 20000 and val not in hits:
                hits.append(val)
    return hits


def score_ocr_candidate(crop_name: str, var_name: str, text: str, value: float) -> float:
    score = 0.0
    combo = f'{crop_name}/{var_name}'.lower()
    text_norm = normalize_ocr_text(text)

    if combo.startswith('jd_price_focus/'):
        score += 7.0
    elif combo.startswith('jd_price_mid/'):
        score += 6.0
    elif combo.startswith('jd_upper_main/'):
        score += 5.0
    elif combo.startswith('jd_desktop_price_area/'):
        score += 4.0
    elif combo.startswith('top_center_price_band/'):
        score += 2.5
    elif combo.startswith('center_band/'):
        score += 1.5
    elif combo.startswith('full_window/'):
        score -= 2.5

    if var_name in ('gray', 'contrast'):
        score += 1.0
    if var_name == 'sharp':
        score += 0.6
    if var_name.startswith('bw'):
        score -= 0.3

    if f'￥{int(value)}' in text_norm or f'￥{value:.2f}' in text_norm:
        score += 3.5
    elif re.search(rf'(?<!\d){int(value)}(?!\d)', text_norm):
        score += 2.0

    if 3000 <= value <= 12000:
        score += 2.0
    return score


def ocr_image_price(image_path: Path) -> Tuple[Optional[float], List[float], List[str], List[str], List[Dict[str, Any]]]:
    img = Image.open(image_path)
    candidates: List[float] = []
    texts: List[str] = []
    saved: List[str] = []
    ranked_hits: List[Dict[str, Any]] = []
    for crop_name, crop in crop_variants(img):
        for var_name, var_img in image_variants(crop):
            out_path = OCR_DEBUG_DIR / f'{image_path.stem}_{crop_name}_{var_name}.png'
            var_img.save(out_path)
            saved.append(out_path.name)
            raw_text = run_tesseract(out_path)
            text = normalize_ocr_text(raw_text)
            if text:
                ocr_vals = extract_ocr_price_candidates(text)
                texts.append(f'[{crop_name}/{var_name}] {text} :: candidates={ocr_vals}')
                for val in ocr_vals:
                    if val not in candidates:
                        candidates.append(val)
                    ranked_hits.append({
                        'crop': crop_name,
                        'variant': var_name,
                        'value': val,
                        'score': score_ocr_candidate(crop_name, var_name, text, val),
                        'text': text[:220],
                    })
    ranked_hits.sort(key=lambda x: x['score'], reverse=True)
    price = ranked_hits[0]['value'] if ranked_hits else pick_best_price(candidates, ' '.join(texts))
    return price, candidates, texts, saved, ranked_hits


def crop_variants(img: Image.Image) -> List[Tuple[str, Image.Image]]:
    w, h = img.size
    boxes = {
        'top_left_price_band': (0, 0, int(w * 0.55), int(h * 0.35)),
        'top_center_price_band': (int(w * 0.15), 0, int(w * 0.85), int(h * 0.4)),
        'center_band': (int(w * 0.05), int(h * 0.1), int(w * 0.9), int(h * 0.55)),
        'jd_desktop_price_area': (int(w * 0.28), int(h * 0.08), int(w * 0.88), int(h * 0.45)),
        'right_price_panel': (int(w * 0.38), int(h * 0.12), int(w * 0.95), int(h * 0.55)),
        'jd_price_focus': (int(w * 0.22), int(h * 0.11), int(w * 0.68), int(h * 0.40)),
        'jd_price_mid': (int(w * 0.27), int(h * 0.13), int(w * 0.75), int(h * 0.48)),
        'jd_upper_main': (int(w * 0.13), int(h * 0.08), int(w * 0.83), int(h * 0.50)),
        'full_window': (0, 0, w, h),
    }
    out = []
    for name, box in boxes.items():
        crop = img.crop(box)
        out.append((name, crop))
    return out


def image_variants(img: Image.Image) -> List[Tuple[str, Image.Image]]:
    gray = ImageOps.grayscale(img)
    variants = [('gray', gray)]
    hi = ImageEnhance.Contrast(gray).enhance(2.5)
    variants.append(('contrast', hi))
    sharp = hi.filter(ImageFilter.SHARPEN)
    variants.append(('sharp', sharp))
    bw = sharp.point(lambda p: 255 if p > 160 else 0)
    variants.append(('bw160', bw))
    bw2 = sharp.point(lambda p: 255 if p > 190 else 0)
    variants.append(('bw190', bw2))
    return variants


def run_tesseract(image_path: Path) -> str:
    import subprocess
    if not TESSERACT_PATH.exists():
        return ''
    cmd = [str(TESSERACT_PATH), str(image_path), 'stdout', '--psm', '6', '-l', 'eng']
    res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    return (res.stdout or '').strip()


def attempt_active_window_ocr(url: str) -> ExtractAttempt:
    if not TESSERACT_PATH.exists():
        return ExtractAttempt(
            name='active_window_ocr',
            ok=False,
            error=f'Tesseract not found: {TESSERACT_PATH}',
            raw_hint='请先安装 Tesseract-OCR，或确认路径 C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
        )
    capture_path, capture_meta = capture_foreground_window()
    trusted_capture = is_trusted_jd_window(str(capture_meta.get('title', '')))
    if not trusted_capture:
        capture_meta['trusted_jd_window'] = False
        capture_meta['warning'] = 'Foreground window title does not look like a JD product page; auto screenshot will not be trusted for price selection.'
    else:
        capture_meta['trusted_jd_window'] = True
    input_paths: List[Path] = []
    if capture_path and capture_path.exists() and trusted_capture:
        input_paths.append(capture_path)
    if OCR_INPUT_PATH.exists() and OCR_INPUT_PATH not in input_paths:
        input_paths.append(OCR_INPUT_PATH)
    if not input_paths:
        return ExtractAttempt(
            name='active_window_ocr',
            ok=False,
            error='No screenshot available',
            raw_hint='请先把真实浏览器打开到京东商品页并置于前台；或手工截图保存为 active_window_price.png 后重跑',
            meta={'capture': capture_meta}
        )
    try:
        best_price: Optional[float] = None
        all_candidates: List[float] = []
        all_texts: List[str] = []
        saved: List[str] = []
        used_input = ''
        per_image: List[Dict[str, Any]] = []
        for image_path in input_paths:
            price, candidates, texts, saved_names, ranked_hits = ocr_image_price(image_path)
            saved.extend(saved_names)
            all_texts.extend([f'{image_path.name}:{x}' for x in texts])
            for val in candidates:
                if val not in all_candidates:
                    all_candidates.append(val)
            per_image.append({
                'path': str(image_path),
                'price': price,
                'candidate_prices': candidates[:20],
                'top_ranked_hits': ranked_hits[:12],
                'text_snip': ' | '.join(texts[:6])[:1200]
            })
            if best_price is None and price is not None:
                best_price = price
                used_input = str(image_path)
        if best_price is None:
            best_price = pick_best_price(all_candidates, ' '.join(all_texts))
            used_input = str(input_paths[0])
        return ExtractAttempt(
            name='active_window_ocr',
            ok=True,
            price=best_price,
            title='active_window_ocr',
            raw_hint=' | '.join(all_texts[:8])[:1200],
            meta={
                'capture': capture_meta,
                'ocr_input': used_input,
                'input_paths': [str(p) for p in input_paths],
                'saved_variants': saved[:30],
                'candidate_prices': all_candidates[:30],
                'per_image': per_image,
            }
        )
    except Exception as e:
        return ExtractAttempt(name='active_window_ocr', ok=False, error=str(e), meta={'capture': capture_meta})


def choose_snapshot(url: str, attempts: List[ExtractAttempt], config: Dict[str, Any]) -> Snapshot:
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_attempts = [sanitize_attempt_price(a, config) for a in attempts]
    priced = [a for a in clean_attempts if a.price is not None]
    if priced:
        priced.sort(key=lambda a: attempt_priority(a.name), reverse=True)
        a = priced[0]
        return Snapshot(
            title=a.title or "未知商品",
            price=a.price,
            store_text=a.store_text,
            in_stock=infer_stock(a.raw_hint + " " + a.price_text),
            url=url,
            fetched_at=fetched_at,
            extractor=a.name,
            raw_hint=a.raw_hint or a.price_text,
            attempts=[asdict(x) for x in clean_attempts],
        )
    best = next((a for a in clean_attempts if a.ok), clean_attempts[0])
    return Snapshot(
        title=best.title or "未知商品",
        price=None,
        store_text=best.store_text,
        in_stock=infer_stock(best.raw_hint + " " + best.price_text),
        url=url,
        fetched_at=fetched_at,
        extractor=best.name,
        raw_hint=best.raw_hint or best.price_text or best.error,
        attempts=[asdict(x) for x in clean_attempts],
    )


def should_notify(config: Dict[str, Any], prev: Dict[str, Any], snap: Snapshot) -> Optional[str]:
    if snap.price is None:
        return None
    baseline = config.get("baseline_price")
    if config.get("only_notify_below_baseline", True) and baseline is not None:
        if snap.price >= float(baseline):
            return None
    prev_price = prev.get("last_price") or baseline
    if prev_price is None:
        if config.get("suppress_first_record_notice", True):
            return None
        return f"首次记录价格：¥{snap.price:.2f}"
    drop = float(prev_price) - snap.price
    if drop >= float(config.get("notify_min_drop", 1.0)):
        return f"真降价 ¥{drop:.2f}（基准/上次 {float(prev_price):.2f} -> {snap.price:.2f}）"
    return None


def send_email(config: Dict[str, Any], subject: str, body: str) -> None:
    smtp_cfg = config["smtp"]
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = smtp_cfg["user"]
    msg["To"] = config["qq_email_to"]
    msg["Subject"] = subject
    smtp = smtplib.SMTP_SSL(smtp_cfg["host"], smtp_cfg["port"])
    smtp.login(smtp_cfg["user"], smtp_cfg["password"])
    smtp.send_message(msg)
    smtp.quit()


def build_attempts(url: str, ocr_only: bool = False) -> List[ExtractAttempt]:
    if ocr_only:
        return [attempt_active_window_ocr(url)]
    return [
        attempt_requests_html(url),
        attempt_requests_with_profile_cookies(url),
        attempt_script_json(url),
        attempt_playwright_dom(url),
        attempt_profile_scan(url),
        attempt_real_session_probe(url),
        attempt_active_window_ocr(url),
    ]


def run_once(config: Dict[str, Any], state: Dict[str, Any], ocr_only: bool = False, dry_run: bool = False) -> Snapshot:
    url = config["product_url"]
    attempts = build_attempts(url, ocr_only=ocr_only)
    snap = choose_snapshot(url, attempts, config)
    append_log(snap)

    note = should_notify(config, state, snap)
    body = build_report_body(config, snap, attempts, note)
    print(body)

    if note and not dry_run:
        send_email(config, f"[盯价提醒] {config['product_name']}", body)

    state.update({
        "last_price": snap.price,
        "last_title": snap.title,
        "last_store_text": snap.store_text,
        "last_in_stock": snap.in_stock,
        "last_fetched_at": snap.fetched_at,
        "last_extractor": snap.extractor,
        "last_note": note or "",
    })
    save_state(state)
    return snap


def build_report_body(config: Dict[str, Any], snap: Snapshot, attempts: List[ExtractAttempt], note: Optional[str]) -> str:
    body = (
        f"商品：{config['product_name']}\n"
        f"页面标题：{snap.title}\n"
        f"当前价格：{('¥%.2f' % snap.price) if snap.price is not None else '未解析到'}\n"
        f"主提取器：{snap.extractor}\n"
        f"店铺线索：{snap.store_text or '未解析到'}\n"
        f"库存：{snap.in_stock}\n"
        f"时间：{snap.fetched_at}\n"
        f"链接：{snap.url}\n"
        f"说明：{note or '本轮未触发降价通知'}\n"
        f"尝试摘要：\n"
    )
    for a in attempts:
        body += f"- {a.name}: ok={a.ok}, price={a.price}, price_text={a.price_text or '空'}, error={a.error or '无'}\n"
        if a.meta:
            body += f"  meta={json.dumps(a.meta, ensure_ascii=False)[:1000]}\n"
    return body


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='京东 iPhone 17 256G 自营价监控')
    parser.add_argument('--ocr-only', action='store_true', help='只运行真实前台窗口截图 OCR，不跑其它网络/浏览器提取器')
    parser.add_argument('--once', action='store_true', help='只运行一次（默认）')
    parser.add_argument('--loop', action='store_true', help='按配置 poll_minutes 循环盯价')
    parser.add_argument('--open-url', action='store_true', help='先用默认浏览器打开京东商品页，等待页面置前后再 OCR')
    parser.add_argument('--wait-seconds', type=int, default=0, help='打开页面或运行前等待多少秒，方便手动登录/切到前台')
    parser.add_argument('--dry-run', action='store_true', help='不发送邮件，只打印和写日志/状态')
    return parser.parse_args()


def run() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    args = parse_args()
    config = ensure_config()
    state = load_state()
    url = config["product_url"]
    if args.open_url:
        webbrowser.open(url)
    if args.wait_seconds > 0:
        print(f'等待 {args.wait_seconds} 秒，请把真实京东商品页放到前台且确认价格可见...')
        time.sleep(args.wait_seconds)

    while True:
        run_once(config, state, ocr_only=args.ocr_only, dry_run=args.dry_run)
        if not args.loop:
            return 0
        sleep_seconds = max(60, int(float(config.get('poll_minutes', 30)) * 60))
        print(f'下一轮将在 {sleep_seconds} 秒后运行。')
        time.sleep(sleep_seconds)


if __name__ == "__main__":
    raise SystemExit(run())
