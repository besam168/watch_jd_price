from pathlib import Path
import re
import json
from html import unescape

path = Path(r"C:\Users\besam\.openclaw\workspace\skills\scrapling-openclaw\output\news.yahoo.com_index_fetch_20260421_094540.html")
t = path.read_text(encoding="utf-8", errors="replace")

results = {
    "reuters_mentions": len(re.findall(r"Reuters", t, re.I)),
    "reuters_links": re.findall(r"https?://[^\"'\s>]*reuters\.com[^\"'\s>]*", t, re.I)[:30],
    "zenfs_reuters_assets": re.findall(r"https?://[^\"'\s>]*reuters\.com[^\"'\s>]*", t, re.I)[:30],
}

# Try to find Yahoo article anchors whose nearby block mentions Reuters
anchors = []
for m in re.finditer(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', t, re.I | re.S):
    href = m.group(1)
    inner = re.sub(r'<[^>]+>', ' ', m.group(2))
    inner = unescape(re.sub(r'\s+', ' ', inner)).strip()
    s = max(0, m.start() - 500)
    e = min(len(t), m.end() + 500)
    chunk = t[s:e]
    if re.search(r'Reuters', chunk, re.I):
        if inner and len(inner) >= 12:
            anchors.append({"title": inner, "url": href})

# dedupe
seen = set()
out = []
for item in anchors:
    key = (item['title'].lower(), item['url'])
    if key in seen:
        continue
    seen.add(key)
    out.append(item)
    if len(out) >= 20:
        break

results['nearby_reuters_items'] = out
print(json.dumps(results, ensure_ascii=False, indent=2))
