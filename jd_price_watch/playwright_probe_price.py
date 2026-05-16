from pathlib import Path
from playwright.sync_api import sync_playwright

URL = 'https://item.jd.com/100278222276.html'
OUT = Path('jd_price_watch') / 'playwright_probe_price.txt'
OUT.parent.mkdir(parents=True, exist_ok=True)

SELECTORS = [
    '.p-price .price',
    '.p-price span.price',
    '.summary-price .p-price .price',
    '[class*=price] i',
    '[class*=price] .price',
    '.dd .p-price',
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 2400}, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36')
    page.goto(URL, wait_until='networkidle', timeout=90000)
    page.wait_for_timeout(8000)
    lines = []
    lines.append('TITLE=' + page.title())
    for sel in SELECTORS:
        try:
            loc = page.locator(sel).first
            txt = loc.inner_text(timeout=3000)
            lines.append(f'SEL={sel} => {txt}')
        except Exception as e:
            lines.append(f'SEL={sel} => ERR: {e}')
    body = page.locator('body').inner_text(timeout=10000)
    idx = body.find('京 东 价')
    lines.append('\nBODY_SNIP=\n' + (body[idx:idx+600] if idx >= 0 else body[:600]))
    html = page.content()
    for needle in ['p-price', 'summary-price', 'J-p-100278222276', 'price']:
        pos = html.find(needle)
        lines.append(f'HTML_FIND {needle} => {pos}')
        if pos >= 0:
            lines.append(html[max(0,pos-250):pos+600])
    OUT.write_text('\n\n'.join(lines), encoding='utf-8')
    print('done')
    browser.close()
