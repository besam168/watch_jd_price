import argparse
import json
import re
from html import unescape
from pathlib import Path


def strip_tags(text: str) -> str:
    text = re.sub(r'<script[\s\S]*?</script>', ' ', text, flags=re.I)
    text = re.sub(r'<style[\s\S]*?</style>', ' ', text, flags=re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def normalize_url(url: str, base: str = '') -> str:
    if not url:
        return ''
    if url.startswith('//'):
        return 'https:' + url
    if url.startswith('http://') or url.startswith('https://'):
        return url
    if base:
        return base.rstrip('/') + '/' + url.lstrip('/')
    return url


def extract_anchors(html: str, base: str = ''):
    anchors = []
    pattern = re.compile(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.I | re.S)
    for href, inner in pattern.findall(html):
        title = strip_tags(inner)
        href = normalize_url(href, base)
        if not title or len(title) < 12:
            continue
        if href.startswith('#') or href.lower().startswith('javascript:'):
            continue
        anchors.append({'title': title, 'url': href})
    return anchors


def score_item(item, source: str):
    title = item['title']
    url = item['url']
    score = 0
    if len(title) >= 18:
        score += 2
    if len(title) >= 35:
        score += 2
    if url.startswith('http'):
        score += 1
    lower_url = url.lower()
    lower_title = title.lower()
    if source == 'reuters':
        if '/world/' in lower_url or '/business/' in lower_url or '/markets/' in lower_url or '/technology/' in lower_url:
            score += 3
    elif source == 'bbc':
        if '/news/' in lower_url:
            score += 3
    elif source == 'aljazeera':
        if '/news/' in lower_url or '/program/' not in lower_url:
            score += 2
    elif source == 'ap':
        if '/article/' in lower_url:
            score += 3
    bad_bits = ['live updates', 'watch live', 'newsletter', 'sign up', 'cookie', 'advertisement', 'video', 'podcast']
    if any(bit in lower_title for bit in bad_bits):
        score -= 4
    return score


def dedupe(items):
    seen = set()
    out = []
    for item in items:
        key = (item['title'].strip().lower(), item['url'].strip().lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def filter_items(items, source: str, limit: int):
    filtered = []
    for item in items:
        scored = dict(item)
        scored['score'] = score_item(item, source)
        if scored['score'] < 2:
            continue
        filtered.append(scored)
    filtered.sort(key=lambda x: (-x['score'], len(x['title'])))
    filtered = dedupe(filtered)
    return filtered[:limit]


def source_from_path(path: Path) -> tuple[str, str]:
    name = path.name.lower()
    if 'reuters' in name:
        return 'reuters', 'https://www.reuters.com'
    if 'bbc' in name:
        return 'bbc', 'https://www.bbc.com'
    if 'aljazeera' in name:
        return 'aljazeera', 'https://www.aljazeera.com'
    if 'apnews' in name:
        return 'ap', 'https://apnews.com'
    return 'unknown', ''


def main():
    parser = argparse.ArgumentParser(description='Extract likely headlines from saved Scrapling HTML files')
    parser.add_argument('--files', nargs='+', required=True)
    parser.add_argument('--per-site', type=int, default=3)
    args = parser.parse_args()

    result = {'ok': True, 'sites': [], 'total_headlines': 0}
    all_count = 0
    for raw in args.files:
        path = Path(raw)
        html = path.read_text(encoding='utf-8', errors='replace')
        source, base = source_from_path(path)
        anchors = extract_anchors(html, base=base)
        picks = filter_items(anchors, source=source, limit=args.per_site)
        result['sites'].append({
            'source': source,
            'file': str(path),
            'headline_count': len(picks),
            'headlines': picks,
        })
        all_count += len(picks)

    result['total_headlines'] = all_count
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
