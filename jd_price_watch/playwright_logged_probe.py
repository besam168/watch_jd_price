from pathlib import Path
from playwright.sync_api import sync_playwright

URL = 'https://item.jd.com/100278222276.html'
OUT = Path('jd_price_watch')
OUT.mkdir(parents=True, exist_ok=True)
SCREEN = OUT / 'jd_logged_probe.png'
TEXT = OUT / 'jd_logged_probe.txt'

CHROME_PROFILE = Path.home() / 'AppData/Local/Google/Chrome/User Data'
EDGE_PROFILE = Path.home() / 'AppData/Local/Microsoft/Edge/User Data'

profile = CHROME_PROFILE if CHROME_PROFILE.exists() else EDGE_PROFILE

with sync_playwright() as p:
    browser_type = p.chromium
    context = browser_type.launch_persistent_context(
        user_data_dir=str(profile),
        headless=True,
        viewport={'width': 1440, 'height': 2400},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36',
    )
    page = context.new_page()
    page.goto(URL, wait_until='networkidle', timeout=90000)
    page.wait_for_timeout(12000)
    body = page.locator('body').inner_text(timeout=10000)
    price_text = ''
    for sel in ['.price.J-p-100278222276', '.p-price .price', '.dd .p-price']:
        try:
            t = page.locator(sel).first.inner_text(timeout=3000)
            price_text += f'{sel} => {t}\n'
        except Exception as e:
            price_text += f'{sel} => ERR {e}\n'
    SCREEN and page.screenshot(path=str(SCREEN), full_page=True)
    TEXT.write_text('TITLE=' + page.title() + '\n\n' + price_text + '\nBODY_SNIP=\n' + body[:2500], encoding='utf-8')
    print('done')
    context.close()
