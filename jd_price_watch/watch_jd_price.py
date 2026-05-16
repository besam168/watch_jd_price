import json
import os
import re
import smtplib
from dataclasses import dataclass
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, Optional

import requests

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = DATA_DIR / "config.json"
STATE_PATH = DATA_DIR / "state.json"
LOG_PATH = DATA_DIR / "price_log.jsonl"

DEFAULT_CONFIG = {
    "product_name": "京东 iPhone 17 256G",
    "product_url": "https://item.jd.com/100149542922.html",
    "allowed_store_keywords": ["自营", "旗舰店", "Apple"],
    "poll_minutes": 30,
    "notify_on_any_drop": True,
    "notify_min_drop": 1.0,
    "qq_email_to": "758622673@qq.com",
    "smtp": {
        "host": "smtp.qq.com",
        "port": 465,
        "user": "910633260@qq.com",
        "password": "sghqeeeeyuzjbcbb"
    }
}


@dataclass
class Snapshot:
    title: str
    price: Optional[float]
    store_text: str
    in_stock: Optional[bool]
    url: str
    fetched_at: str
    raw_hint: str = ""



def ensure_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2), encoding="utf-8")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))



def load_state() -> Dict[str, Any]:
    if not STATE_PATH.exists():
        return {}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))



def save_state(state: Dict[str, Any]) -> None:
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")



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
    title = re.sub(r"\s+", " ", m.group(1)).strip()
    return title



def extract_price(html: str) -> Optional[float]:
    patterns = [
        r'"price"\s*:\s*"([0-9]+(?:\.[0-9]+)?)"',
        r'price[:=]\s*"?([0-9]+(?:\.[0-9]+)?)"?',
        r'jdPrice[:=]\s*"?([0-9]+(?:\.[0-9]+)?)"?',
        r'¥\s*([0-9]+(?:\.[0-9]+)?)',
    ]
    for p in patterns:
        m = re.search(p, html, re.I)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
    return None



def extract_store_text(html: str) -> str:
    for keyword in ["自营", "旗舰店", "Apple", "京东"]:
        idx = html.find(keyword)
        if idx >= 0:
            snippet = html[max(0, idx - 60): idx + 120]
            snippet = re.sub(r"<[^>]+>", " ", snippet)
            snippet = re.sub(r"\s+", " ", snippet).strip()
            return snippet[:120]
    return ""



def infer_stock(html: str) -> Optional[bool]:
    if "无货" in html:
        return False
    if any(x in html for x in ["有货", "现货", "立即购买", "加入购物车"]):
        return True
    return None



def fetch_snapshot(config: Dict[str, Any]) -> Snapshot:
    html = fetch_html(config["product_url"])
    title = extract_title(html)
    price = extract_price(html)
    store_text = extract_store_text(html)
    in_stock = infer_stock(html)
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    raw_hint = f"title={title}; store={store_text}; price={price}; stock={in_stock}"
    return Snapshot(title=title, price=price, store_text=store_text, in_stock=in_stock, url=config["product_url"], fetched_at=fetched_at, raw_hint=raw_hint)



def append_log(snapshot: Snapshot) -> None:
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot.__dict__, ensure_ascii=False) + "\n")



def should_notify(config: Dict[str, Any], prev: Dict[str, Any], snap: Snapshot) -> Optional[str]:
    if snap.price is None:
        return None
    prev_price = prev.get("last_price")
    if prev_price is None:
        return f"首次记录价格：¥{snap.price:.2f}"
    drop = float(prev_price) - snap.price
    if drop >= float(config.get("notify_min_drop", 1.0)):
        return f"价格下降 ¥{drop:.2f}（{prev_price:.2f} -> {snap.price:.2f}）"
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



def run() -> int:
    config = ensure_config()
    state = load_state()
    snap = fetch_snapshot(config)
    append_log(snap)

    note = should_notify(config, state, snap)
    body = (
        f"商品：{config['product_name']}\n"
        f"页面标题：{snap.title}\n"
        f"当前价格：{('¥%.2f' % snap.price) if snap.price is not None else '未解析到'}\n"
        f"店铺线索：{snap.store_text or '未解析到'}\n"
        f"库存：{snap.in_stock}\n"
        f"时间：{snap.fetched_at}\n"
        f"链接：{snap.url}\n"
        f"说明：{note or '价格无变化'}\n"
    )

    print(body)

    if note:
        send_email(config, f"[盯价提醒] {config['product_name']}", body)

    state.update({
        "last_price": snap.price,
        "last_title": snap.title,
        "last_store_text": snap.store_text,
        "last_in_stock": snap.in_stock,
        "last_fetched_at": snap.fetched_at,
    })
    save_state(state)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
