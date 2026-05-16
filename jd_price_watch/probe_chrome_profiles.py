from pathlib import Path
import json
from playwright.sync_api import sync_playwright

base = Path.home() / 'AppData/Local/Google/Chrome/User Data'
out = Path(r'C:\Users\besam\.openclaw\workspace\jd_price_watch\chrome_profiles_probe.json')
url = 'https://item.jd.com/100278222276.html'
profiles = []
if base.exists():
    for p in sorted(base.iterdir()):
        if p.is_dir() and (p.name == 'Default' or p.name.startswith('Profile')):
            profiles.append(p)
results = []

with sync_playwright() as pw:
    for prof in profiles[:12]:
        item = {'profile': prof.name}
        try:
            ctx = pw.chromium.launch_persistent_context(
                user_data_dir=str(prof),
                headless=True,
                viewport={'width': 1440, 'height': 2400},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36',
            )
            page = ctx.new_page()
            page.goto(url, wait_until='networkidle', timeout=90000)
            page.wait_for_timeout(8000)
            title = page.title()
            body = page.locator('body').inner_text(timeout=10000)
            try:
                price = page.locator('.price.J-p-100278222276').first.inner_text(timeout=3000).strip()
            except Exception:
                price = ''
            try:
                pprice = page.locator('.p-price').first.inner_text(timeout=3000).strip()
            except Exception:
                pprice = ''
            item.update({
                'title': title,
                'price': price,
                'p_price': pprice,
                'has_login_words': any(k in body for k in ['退出登录','我的京东','账户设置','订单中心']),
                'has_price_digits': any(x in body for x in ['5999','5369','5469']),
                'body_snip': body[:1200],
            })
            ctx.close()
        except Exception as e:
            item['error'] = repr(e)
        results.append(item)

out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print(out)
