import json
import re
import smtplib
from dataclasses import dataclass
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = DATA_DIR / 'config.json'
STATE_PATH = DATA_DIR / 'state_playwright.json'
SCREENSHOT_PATH = BASE_DIR / 'latest_page.png'

CHROME_PROFILE = Path.home() / 'AppData/Local/Google/Chrome/User Data'
EDGE_PROFILE = Path.home() / 'AppData/Local/Microsoft/Edge/User Data'

@dataclass
class Snapshot:
    title: str
    store: str
    price_text: str
    url: str
    fetched_at: str
    body_snip: str


def load_config():
    return json.loads(CONFIG_PATH.read_text(encoding='utf-8'))


def load_state():
    if not STATE_PATH.exists():
        return {}
    return json.loads(STATE_PATH.read_text(encoding='utf-8'))


def save_state(state):
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')


def pick_profile() -> Optional[Path]:
    if CHROME_PROFILE.exists():
        return CHROME_PROFILE
    if EDGE_PROFILE.exists():
        return EDGE_PROFILE
    return None


def fetch_snapshot(url: str) -> Snapshot:
    profile = pick_profile()
    if profile is None:
        raise RuntimeError('No browser profile found')

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile),
            headless=True,
            viewport={'width': 1440, 'height': 2400},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36',
        )
        page = context.new_page()
        page.goto(url, wait_until='networkidle', timeout=90000)
        page.wait_for_timeout(12000)
        title = page.title()
        body = page.locator('body').inner_text(timeout=10000)
        try:
            store = page.locator('text=Apple产品京东自营旗舰店').first.inner_text(timeout=3000)
        except Exception:
            store = ''
        price_candidates = []
        for sel in ['.price.J-p-100278222276', '.p-price .price', '.dd .p-price']:
            try:
                txt = page.locator(sel).first.inner_text(timeout=3000).strip()
                if txt:
                    price_candidates.append((sel, txt))
            except Exception:
                pass
        price_text = ' | '.join(f'{s}={t}' for s, t in price_candidates)
        page.screenshot(path=str(SCREENSHOT_PATH), full_page=True)
        context.close()
    return Snapshot(
        title=title,
        store=store,
        price_text=price_text,
        url=url,
        fetched_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        body_snip=body[:2000],
    )


def extract_price_number(price_text: str) -> Optional[float]:
    m = re.search(r'([0-9]{3,5}(?:\.[0-9]{1,2})?)', price_text)
    return float(m.group(1)) if m else None


def send_email(config, subject: str, body: str):
    smtp_cfg = config['smtp']
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['From'] = smtp_cfg['user']
    msg['To'] = config['qq_email_to']
    msg['Subject'] = subject
    smtp = smtplib.SMTP_SSL(smtp_cfg['host'], smtp_cfg['port'])
    smtp.login(smtp_cfg['user'], smtp_cfg['password'])
    smtp.send_message(msg)
    smtp.quit()


def main():
    config = load_config()
    state = load_state()
    snap = fetch_snapshot(config['product_url'])
    price = extract_price_number(snap.price_text)
    prev_price = state.get('last_price')
    note = '未取到价格数字；需人工确认浏览器中是否已显示价格。'
    if price is not None and prev_price is None:
        note = f'首次记录价格：¥{price:.2f}'
    elif price is not None and prev_price is not None and price < prev_price:
        note = f'价格下降：¥{prev_price:.2f} -> ¥{price:.2f}'
        send_email(config, f"[盯价提醒] {config['product_name']}", note + f"\n时间：{snap.fetched_at}\n链接：{snap.url}")
    elif price is not None and prev_price is not None:
        note = f'价格未下降：当前 ¥{price:.2f}，上次 ¥{prev_price:.2f}'

    report = (
        f'商品：{config["product_name"]}\n'
        f'标题：{snap.title}\n'
        f'店铺：{snap.store or "未识别到"}\n'
        f'价格文本：{snap.price_text or "空"}\n'
        f'时间：{snap.fetched_at}\n'
        f'说明：{note}\n'
        f'链接：{snap.url}\n'
    )
    print(report)
    state.update({
        'last_price': price,
        'last_title': snap.title,
        'last_store': snap.store,
        'last_price_text': snap.price_text,
        'last_fetched_at': snap.fetched_at,
        'last_note': note,
    })
    save_state(state)


if __name__ == '__main__':
    main()
