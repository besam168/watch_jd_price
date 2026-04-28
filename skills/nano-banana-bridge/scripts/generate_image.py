import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / 'output'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_output_path(prefix: str = 'nano-banana') -> Path:
    stamp = time.strftime('%Y%m%d_%H%M%S')
    return OUTPUT_DIR / f'{prefix}_{stamp}.png'


def normalize_base_url(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip().replace('\\v1', '/v1')
    value = value.rstrip('/')
    return value


def infer_extension_from_url(url: str) -> str:
    path = urlparse(url).path.lower()
    for ext in ('.png', '.jpg', '.jpeg', '.webp'):
        if path.endswith(ext):
            return '.jpg' if ext == '.jpeg' else ext
    return '.png'


def http_json(url: str, payload: dict, headers: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = resp.read().decode('utf-8', errors='replace')
        return json.loads(body)


def download_binary(url: str) -> bytes:
    req = urllib.request.Request(url, method='GET')
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def generate_openai_compatible(prompt: str, size: str, model: str, base_url: str, api_key: str, output_path: Path) -> dict:
    endpoint = f'{base_url}/images/generations'
    payload = {
        'model': model,
        'prompt': prompt,
        'size': size,
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }

    data = http_json(endpoint, payload, headers)
    items = data.get('data') or []
    if not items:
        raise RuntimeError(f'No image data returned from provider: {data}')

    first = items[0]
    if first.get('b64_json'):
        output_path.write_bytes(base64.b64decode(first['b64_json']))
        source_mode = 'b64_json'
    elif first.get('url'):
        actual_ext = infer_extension_from_url(first['url'])
        actual_output = output_path.with_suffix(actual_ext)
        actual_output.write_bytes(download_binary(first['url']))
        output_path = actual_output
        source_mode = 'url'
    else:
        raise RuntimeError(f'Unsupported provider response shape: {first}')

    return {
        'status': 'ok',
        'mode': 'openai-compatible',
        'prompt': prompt,
        'inputImage': None,
        'output': str(output_path),
        'size': size,
        'provider': 'openai-compatible',
        'model': model,
        'baseUrl': base_url,
        'responseSource': source_mode,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Nano Banana style image generation bridge skeleton')
    parser.add_argument('--prompt', required=True, help='Text prompt for generation/editing')
    parser.add_argument('--input-image', help='Optional input image path for image-to-image/edit mode')
    parser.add_argument('--size', default='1024x1024', help='Output size, e.g. 1024x1024 or 1536x1024')
    parser.add_argument('--provider', default='mock', help='Provider name: mock | openai-compatible')
    parser.add_argument('--base-url', help='Base URL for provider, e.g. https://api-cn.hi-code.cc/v1')
    parser.add_argument('--api-key', help='API key for provider')
    parser.add_argument('--model', help='Model name for provider')
    parser.add_argument('--mock', action='store_true', help='Run in mock mode')
    parser.add_argument('--dry-run', action='store_true', help='Only print planned action, do not generate file')
    args = parser.parse_args()

    input_image = str(Path(args.input_image).resolve()) if args.input_image else None
    output_path = build_output_path()

    base_url = normalize_base_url(args.base_url or os.environ.get('OPENAI_IMAGE_BASE_URL'))
    api_key = args.api_key or os.environ.get('OPENAI_IMAGE_API_KEY')
    model = args.model or os.environ.get('OPENAI_IMAGE_MODEL') or 'gpt-image-1'

    if args.dry_run:
        print(json.dumps({
            'status': 'ok',
            'mode': 'dry-run',
            'prompt': args.prompt,
            'inputImage': input_image,
            'output': str(output_path),
            'size': args.size,
            'provider': args.provider,
            'model': model,
            'baseUrl': base_url,
        }, ensure_ascii=False, indent=2))
        return 0

    if args.mock or args.provider == 'mock':
        output_path.write_bytes(b'')
        print(json.dumps({
            'status': 'ok',
            'mode': 'mock',
            'prompt': args.prompt,
            'inputImage': input_image,
            'output': str(output_path),
            'size': args.size,
            'provider': 'mock',
            'note': 'Skeleton bridge mock output. Switch to --provider openai-compatible for real generation.'
        }, ensure_ascii=False, indent=2))
        return 0

    if args.provider == 'openai-compatible':
        if input_image:
            print(json.dumps({
                'status': 'error',
                'error': 'input-image is not implemented yet for openai-compatible mode in this script.'
            }, ensure_ascii=False, indent=2))
            return 1
        if not base_url:
            print(json.dumps({
                'status': 'error',
                'error': 'Missing base URL. Use --base-url or OPENAI_IMAGE_BASE_URL.'
            }, ensure_ascii=False, indent=2))
            return 1
        if not api_key:
            print(json.dumps({
                'status': 'error',
                'error': 'Missing API key. Use --api-key or OPENAI_IMAGE_API_KEY.'
            }, ensure_ascii=False, indent=2))
            return 1

        try:
            result = generate_openai_compatible(
                prompt=args.prompt,
                size=args.size,
                model=model,
                base_url=base_url,
                api_key=api_key,
                output_path=output_path,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        except urllib.error.HTTPError as e:
            details = e.read().decode('utf-8', errors='replace')
            print(json.dumps({
                'status': 'error',
                'error': f'HTTP {e.code} calling provider',
                'details': details,
            }, ensure_ascii=False, indent=2))
            return 1
        except Exception as e:
            print(json.dumps({
                'status': 'error',
                'error': str(e),
            }, ensure_ascii=False, indent=2))
            return 1

    print(json.dumps({
        'status': 'error',
        'error': f'Unsupported provider: {args.provider}'
    }, ensure_ascii=False, indent=2))
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
