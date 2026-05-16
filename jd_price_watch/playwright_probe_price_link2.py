from pathlib import Path
from playwright.sync_api import sync_playwright

URL = r'https://item.jd.com/100278222276.html?pcdk=OGyEuQFDnBZKjN1Lwf44kzEIqEIYsGHDMhyKh5FTBz07VNlGYhqIBVZ3XyaDVQBm.3z6a.aI3x&spmTag=YTAyMTkuYjAwMjM1Ni5jMDAwMDcyMTAua2V5d29yZF9lbnRlciU0MDE3NzgyMDIzNjY3ODAlMjMxMjQ1ODYzNzE3JTIzMTc5MTM3MjQ2OCUyQ2EwMjQwLmIwMDI0OTMuYzAwMDA0MDI3LjIlMjNza3VfY2FyZCU0MDE3NzgyMDIzNzE4MzYlMjMxMjQ1ODYzNzE3JTIzMjUzMDUwMDU1'
OUT = Path('jd_price_watch') / 'playwright_probe_price_link2.txt'
OUT.parent.mkdir(parents=True, exist_ok=True)
SELECTORS = ['.price.J-p-100278222276', '.p-price .price', '.dd .p-price']

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 2400}, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36')
    page.goto(URL, wait_until='networkidle', timeout=90000)
    page.wait_for_timeout(12000)
    lines = ['TITLE=' + page.title()]
    for sel in SELECTORS:
        try:
            txt = page.locator(sel).first.inner_text(timeout=5000)
            lines.append(f'{sel} => {txt}')
        except Exception as e:
            lines.append(f'{sel} => ERR: {e}')
    body = page.locator('body').inner_text(timeout=10000)
    idx = body.find('京 东 价')
    lines.append('\nBODY_SNIP=\n' + (body[idx:idx+500] if idx >= 0 else body[:500]))
    OUT.write_text('\n'.join(lines), encoding='utf-8')
    print('done')
    browser.close()
