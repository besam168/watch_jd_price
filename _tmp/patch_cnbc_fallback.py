from pathlib import Path
p=Path(r'C:\Users\besam\.openclaw\workspace\formal_global_intel_report.py')
s=p.read_text(encoding='utf-8')
insert='''

def fallback_cnbc_world(limit: int = 16):
    text = fetch_text("https://www.cnbc.com/world/?region=world", timeout=20)
    items = []
    seen = set()
    patterns = [
        r'\[(.*?)\]\((https://www\\.cnbc\\.com/2026/[^)]+)\)',
        r'## \[(.*?)\]\((https://www\\.cnbc\\.com/2026/[^)]+)\)',
    ]
    for pat in patterns:
        for title, link in re.findall(pat, text, flags=re.S):
            title = strip_html(title)
            link = link.strip()
            key = (title, link)
            if not title or key in seen:
                continue
            seen.add(key)
            items.append({"title": title, "link": link, "summary": title, "published": NOW.strftime("%a, %d %b %Y %H:%M:%S GMT"), "published_dt": NOW})
            if len(items) >= limit:
                return items
    return items
'''
anchor='def fallback_reuters(limit: int = 16):\n'
pos=s.index(anchor)
s=s[:pos]+insert+s[pos:]
s=s.replace('{"name": "CNN Business", "url": "http://rss.cnn.com/rss/money_latest.rss", "section": "财经市场"},','{"name": "CNN Business", "url": "http://rss.cnn.com/rss/money_latest.rss", "section": "财经市场"},')
s=s.replace('{"name": "CNBC世界", "url": "https://www.cnbc.com/world/?region=world", "section": "财经市场"},','{"name": "CNBC世界", "url": "https://www.cnbc.com/world/?region=world", "section": "财经市场", "fallback_kind": "cnbc_world"},')
s=s.replace('    if kind == "reuters_page":\n        return fallback_reuters(limit=limit)\n    if kind == "ap":\n        return fallback_ap(limit=limit)\n    raise ValueError(f"unknown fallback kind: {kind}")\n','    if kind == "reuters_page":\n        return fallback_reuters(limit=limit)\n    if kind == "ap":\n        return fallback_ap(limit=limit)\n    if kind == "cnbc_world":\n        return fallback_cnbc_world(limit=limit)\n    raise ValueError(f"unknown fallback kind: {kind}")\n')
p.write_text(s,encoding='utf-8')
print('CNBC_FALLBACK_PATCHED')
