from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r'C:\Users\besam\.openclaw\workspace\jd_price_watch\jd_deep_probe.txt')
URL = 'https://item.jd.com/100278222276.html'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 2400}, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36')
    responses = []

    def on_response(resp):
        try:
            u = resp.url
            if any(k in u for k in ['wareBusiness', 'price', 'sku', 'item', 'api.m.jd.com', 'pc_detailpage']):
                responses.append((resp.status, u))
        except Exception:
            pass

    page.on('response', on_response)
    page.goto(URL, wait_until='networkidle', timeout=90000)
    page.wait_for_timeout(10000)

    lines = []
    lines.append('TITLE=' + page.title())
    try:
        obj = page.evaluate("""
        () => {
          const keys = Object.keys(window).filter(k => /price|Price|sku|ware|item/i.test(k)).slice(0,200);
          const out = {};
          for (const k of keys) {
            try {
              const v = window[k];
              if (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean') out[k] = v;
              else if (v && typeof v === 'object') out[k] = JSON.stringify(v).slice(0,500);
            } catch (e) {}
          }
          return out;
        }
        """)
        lines.append('WINDOW_KEYS=' + str(obj))
    except Exception as e:
        lines.append('WINDOW_KEYS_ERR=' + repr(e))

    for expr in [
        "document.querySelector('.price.J-p-100278222276')?.innerText",
        "document.querySelector('.p-price')?.innerText",
        "document.querySelector('body')?.innerText.includes('5999')",
        "document.querySelector('body')?.innerText.includes('5369')",
    ]:
        try:
            v = page.evaluate(f'() => {expr}')
            lines.append(expr + ' => ' + repr(v))
        except Exception as e:
            lines.append(expr + ' => ERR ' + repr(e))

    lines.append('RESPONSES=')
    for status, u in responses:
        lines.append(f'{status} {u}')

    OUT.write_text('\n'.join(lines), encoding='utf-8')
    print(OUT)
    browser.close()
