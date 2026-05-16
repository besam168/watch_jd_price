from pathlib import Path
from playwright.sync_api import sync_playwright

URL = 'https://item.jd.com/100278222276.html'
OUT = Path('jd_price_watch') / 'playwright_probe.txt'
OUT.parent.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 2200}, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36')
    page.goto(URL, wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(5000)
    title = page.title()
    text = page.locator('body').inner_text(timeout=10000)
    html = page.content()
    OUT.write_text('TITLE:\n' + title + '\n\nBODY:\n' + text[:8000] + '\n\nHTML_SNIP:\n' + html[:8000], encoding='utf-8')
    print('TITLE', title)
    print('TEXT_LEN', len(text))
    browser.close()
