import argparse
import json
import re
import subprocess
import sys
from html import unescape
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / 'output'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RUNNER = BASE_DIR / 'scripts' / 'run_scrapling.py'

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def run_yahoo_fetch():
    cmd = [
        sys.executable,
        str(RUNNER),
        '--url', 'https://news.yahoo.com/',
        '--mode', 'fetch',
        '--format', 'html',
        '--wait-ms', '5000',
        '--network-idle',
        '--real-chrome',
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr[-2000:] or completed.stdout[-2000:] or 'Yahoo fetch failed')
    data = json.loads(completed.stdout)
    if not data.get('ok'):
        raise RuntimeError(data.get('error') or 'Yahoo fetch failed')
    return data


def normalize_url(url: str) -> str:
    if not url:
        return ''
    if url.startswith('http://') or url.startswith('https://'):
        return url
    if url.startswith('//'):
        return 'https:' + url
    if url.startswith('/'):
        return 'https://news.yahoo.com' + url
    return 'https://news.yahoo.com/' + url.lstrip('/')


def extract_reuters_items(html_text: str, limit: int):
    anchors = []
    for m in re.finditer(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html_text, re.I | re.S):
        href = normalize_url(m.group(1))
        inner = re.sub(r'<[^>]+>', ' ', m.group(2))
        inner = unescape(re.sub(r'\s+', ' ', inner)).strip()
        if not inner or len(inner) < 18:
            continue
        s = max(0, m.start() - 700)
        e = min(len(html_text), m.end() + 700)
        chunk = html_text[s:e]
        if not re.search(r'Reuters', chunk, re.I):
            continue
        score = 0
        if '/news/articles/' in href:
            score += 4
        if len(inner) >= 35:
            score += 2
        if 'Exclusive-' in inner or 'sources say' in inner.lower():
            score += 2
        anchors.append({'title': inner, 'url': href, 'score': score})

    seen = set()
    out = []
    anchors.sort(key=lambda x: (-x['score'], -len(x['title'])))
    for item in anchors:
        key = (item['title'].strip().lower(), item['url'].strip().lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
        if len(out) >= limit:
            break
    return out


def main():
    parser = argparse.ArgumentParser(description='Reuters fallback via Yahoo News aggregation')
    parser.add_argument('--limit', type=int, default=12)
    args = parser.parse_args()

    yahoo = run_yahoo_fetch()
    html_text = yahoo.get('content', '')
    items = extract_reuters_items(html_text, limit=args.limit)

    result = {
        'ok': True,
        'source': 'yahoo-news-fallback',
        'target': 'reuters',
        'count': len(items),
        'items': items,
        'upstream_output_file': yahoo.get('output_file'),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
