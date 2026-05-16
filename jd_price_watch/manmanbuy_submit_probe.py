from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r'C:\Users\besam\.openclaw\workspace\jd_price_watch\manmanbuy_submit_probe.txt')
URL = 'https://tool.manmanbuy.com/HistoryLowest.aspx?url=https://item.jd.com/100278222276.html'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 2200}, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36')
    lines = []
    try:
        page.goto(URL, wait_until='networkidle', timeout=90000)
        page.wait_for_timeout(5000)
        lines.append('TITLE1=' + page.title())
        body1 = page.locator('body').inner_text(timeout=10000)
        lines.append('BODY1=' + body1[:3000].replace('\n',' | '))
        # try form submission if input/button present
        filled = False
        for sel in ['input[type=text]', 'input[name=url]', '#url']:
            try:
                page.locator(sel).first.fill('https://item.jd.com/100278222276.html', timeout=3000)
                lines.append('FILLED=' + sel)
                filled = True
                break
            except Exception:
                pass
        if filled:
            for bsel in ['button', 'input[type=submit]', '.btn', '#btnSearch']:
                try:
                    page.locator(bsel).first.click(timeout=3000)
                    lines.append('CLICKED=' + bsel)
                    break
                except Exception:
                    pass
            page.wait_for_timeout(8000)
            lines.append('TITLE2=' + page.title())
            body2 = page.locator('body').inner_text(timeout=10000)
            lines.append('BODY2=' + body2[:4000].replace('\n',' | '))
        OUT.write_text('\n'.join(lines), encoding='utf-8')
        print(OUT)
    finally:
        browser.close()
