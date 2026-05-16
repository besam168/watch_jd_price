from pathlib import Path
from playwright.sync_api import sync_playwright

URL = 'https://item.jd.com/100278222276.html'
OUT = Path('jd_price_watch') / 'network_probe.txt'
OUT.parent.mkdir(parents=True, exist_ok=True)
logs = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 2400}, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36')

    def on_response(resp):
        url = resp.url
        if any(k in url for k in ['price', 'p.3.cn', 'api.m.jd.com', 'item-v3', 'pc_item', 'mgets']):
            logs.append(f'{resp.status} {url}')

    page.on('response', on_response)
    page.goto(URL, wait_until='networkidle', timeout=90000)
    page.wait_for_timeout(8000)
    OUT.write_text('\n'.join(logs), encoding='utf-8')
    print('responses', len(logs))
    browser.close()
