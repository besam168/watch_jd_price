import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / 'output'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def slug_from_url(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.netloc or 'site').replace(':', '_')
    path = parsed.path.strip('/').replace('/', '_') or 'index'
    raw = f"{host}_{path}"
    raw = re.sub(r'[^A-Za-z0-9._-]+', '_', raw)
    return raw[:120]


def build_command(args, mode: str, output_file: Path):
    base = ['scrapling', 'extract']
    if mode == 'get':
        cmd = base + ['get', args.url, str(output_file)]
        if args.timeout_seconds:
            cmd += ['--timeout', str(args.timeout_seconds)]
        if args.css_selector:
            cmd += ['--css-selector', args.css_selector]
        if args.ai_targeted:
            cmd += ['--ai-targeted']
        if args.impersonate:
            cmd += ['--impersonate', args.impersonate]
        if args.no_verify:
            cmd += ['--no-verify']
        if args.no_follow_redirects:
            cmd += ['--no-follow-redirects']
    elif mode == 'fetch':
        cmd = base + ['fetch', args.url, str(output_file)]
        cmd += ['--timeout', str(args.timeout_ms)]
        if args.wait_ms:
            cmd += ['--wait', str(args.wait_ms)]
        if args.css_selector:
            cmd += ['--css-selector', args.css_selector]
        if args.wait_selector:
            cmd += ['--wait-selector', args.wait_selector]
        if args.network_idle:
            cmd += ['--network-idle']
        if args.disable_resources:
            cmd += ['--disable-resources']
        if args.block_ads:
            cmd += ['--block-ads']
        if args.real_chrome:
            cmd += ['--real-chrome']
        if args.ai_targeted:
            cmd += ['--ai-targeted']
    elif mode == 'stealthy':
        cmd = base + ['stealthy-fetch', args.url, str(output_file)]
        cmd += ['--timeout', str(args.timeout_ms)]
        if args.wait_ms:
            cmd += ['--wait', str(args.wait_ms)]
        if args.css_selector:
            cmd += ['--css-selector', args.css_selector]
        if args.wait_selector:
            cmd += ['--wait-selector', args.wait_selector]
        if args.network_idle:
            cmd += ['--network-idle']
        if args.disable_resources:
            cmd += ['--disable-resources']
        if args.block_ads:
            cmd += ['--block-ads']
        if args.real_chrome:
            cmd += ['--real-chrome']
        if args.solve_cloudflare:
            cmd += ['--solve-cloudflare']
        if args.block_webrtc:
            cmd += ['--block-webrtc']
        if args.hide_canvas:
            cmd += ['--hide-canvas']
        if args.ai_targeted:
            cmd += ['--ai-targeted']
    else:
        raise ValueError(f'Unsupported mode: {mode}')

    if args.proxy:
        cmd += ['--proxy', args.proxy]
    return cmd


def run_once(cmd):
    completed = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return {
        'returncode': completed.returncode,
        'stdout': completed.stdout,
        'stderr': completed.stderr,
    }


def read_output(path: Path) -> str:
    if not path.exists():
        return ''
    try:
        return path.read_text(encoding='utf-8', errors='replace')
    except Exception:
        return ''


def auto_modes():
    return ['get', 'fetch', 'stealthy']


def main():
    parser = argparse.ArgumentParser(description='OpenClaw wrapper for local Scrapling CLI')
    parser.add_argument('--url', required=True)
    parser.add_argument('--mode', default='auto', choices=['auto', 'get', 'fetch', 'stealthy'])
    parser.add_argument('--format', default='md', choices=['md', 'html', 'txt'])
    parser.add_argument('--css-selector')
    parser.add_argument('--wait-selector')
    parser.add_argument('--wait-ms', type=int, default=0)
    parser.add_argument('--timeout-ms', type=int, default=30000)
    parser.add_argument('--timeout-seconds', type=int, default=30)
    parser.add_argument('--proxy')
    parser.add_argument('--impersonate')
    parser.add_argument('--ai-targeted', action='store_true')
    parser.add_argument('--network-idle', action='store_true')
    parser.add_argument('--disable-resources', action='store_true')
    parser.add_argument('--block-ads', action='store_true')
    parser.add_argument('--real-chrome', action='store_true')
    parser.add_argument('--solve-cloudflare', action='store_true')
    parser.add_argument('--block-webrtc', action='store_true')
    parser.add_argument('--hide-canvas', action='store_true')
    parser.add_argument('--no-verify', action='store_true')
    parser.add_argument('--no-follow-redirects', action='store_true')
    args = parser.parse_args()

    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    slug = slug_from_url(args.url)
    ext = args.format
    modes = auto_modes() if args.mode == 'auto' else [args.mode]
    fallbacks = []
    final = None

    for mode in modes:
        output_file = OUTPUT_DIR / f'{slug}_{mode}_{stamp}.{ext}'
        cmd = build_command(args, mode, output_file)
        result = run_once(cmd)
        content = read_output(output_file)
        item = {
            'mode': mode,
            'command': cmd,
            'returncode': result['returncode'],
            'stderr': result['stderr'][-4000:],
            'stdout': result['stdout'][-2000:],
            'output_file': str(output_file),
            'content_length': len(content),
        }
        fallbacks.append(item)
        if result['returncode'] == 0 and content.strip():
            final = {
                'ok': True,
                'url': args.url,
                'mode_used': mode,
                'format': args.format,
                'output_file': str(output_file),
                'content': content,
                'content_length': len(content),
                'fallbacks_tried': fallbacks,
            }
            break

    if final is None:
        final = {
            'ok': False,
            'url': args.url,
            'mode_used': None,
            'format': args.format,
            'output_file': None,
            'content': '',
            'content_length': 0,
            'fallbacks_tried': fallbacks,
            'error': 'All Scrapling modes failed or produced empty output',
        }
        print(json.dumps(final, ensure_ascii=False, indent=2))
        sys.exit(1)

    print(json.dumps(final, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
