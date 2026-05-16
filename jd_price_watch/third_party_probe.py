from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r'C:\Users\besam\.openclaw\workspace\jd_price_watch\third_party_probe.txt')
URLS = [
    'https://www.gwdang.com/search?key=100278222276',
    'https://m.gwdang.com/search?key=100278222276',
    'https://tool.manmanbuy.com/m/disSitePro.aspx?c_from=m&url=https://item.jd.com/100278222276.html',
    'https://tool.manmanbuy.com/HistoryLowest.aspx?url=https://item.jd.com/100278222276.html',
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 2200}, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36')
    lines = []
    for url in URLS:
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(5000)
            title = page.title()
            body = page.locator('body').inner_text(timeout=10000)
            lines.append('URL=' + url)
            lines.append('TITLE=' + title)
            lines.append('BODY=' + body[:2000].replace('\n',' | '))
            lines.append('---')
        except Exception as e:
            lines.append('URL=' + url)
            lines.append('ERR=' + repr(e))
            lines.append('---')
    OUT.write_text('\n'.join(lines), encoding='utf-8')
    print(OUT)
    browser.close()
