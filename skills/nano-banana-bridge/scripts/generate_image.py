import argparse
import base64
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / 'output'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ASPECT_RATIO_TO_SIZE = {
    '1:1': {'1K': '1024x1024', '2K': '2048x2048', '4K': '4096x4096'},
    '3:2': {'1K': '1536x1024', '2K': '2304x1536', '4K': '4608x3072'},
    '2:3': {'1K': '1024x1536', '2K': '1536x2304', '4K': '3072x4608'},
    '16:9': {'1K': '1792x1024', '2K': '2048x1152', '4K': '4096x2304'},
    '9:16': {'1K': '1024x1792', '2K': '1152x2048', '4K': '2304x4096'},
    '4:3': {'1K': '1365x1024', '2K': '2731x2048', '4K': '5461x4096'},
    '3:4': {'1K': '1024x1365', '2K': '2048x2731', '4K': '4096x5461'},
    '21:9': {'1K': '2389x1024', '2K': '4779x2048', '4K': '9557x4096'},
}

OPENAI_LEGAL_SIZES = {
    '1024x1024',
    '1024x1536',
    '1536x1024',
}


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


def normalize_openai_size(size: str) -> str:
    if size in OPENAI_LEGAL_SIZES:
        return size

    try:
        width_s, height_s = size.lower().split('x', 1)
        width = int(width_s)
        height = int(height_s)
    except Exception as exc:
        raise ValueError(f'Invalid size: {size}') from exc

    landscape = width >= height
    if abs(width - height) <= min(width, height) * 0.1:
        return '1024x1024'
    return '1536x1024' if landscape else '1024x1536'


def resolve_size(explicit_size: str | None, aspect_ratio: str | None, resolution: str | None) -> str:
    if explicit_size:
        return explicit_size
    if aspect_ratio and resolution:
        try:
            return ASPECT_RATIO_TO_SIZE[aspect_ratio][resolution]
        except KeyError:
            raise ValueError(f'Unsupported aspect-ratio/resolution combination: {aspect_ratio} + {resolution}')
    if aspect_ratio and not resolution:
        raise ValueError('aspect-ratio was provided without resolution. Use --resolution 1K|2K|4K together.')
    if resolution and not aspect_ratio:
        raise ValueError('resolution was provided without aspect-ratio. Use --aspect-ratio together.')
    return '1024x1024'


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


def save_image_result(image_payload: str, output_path: Path) -> tuple[Path, str]:
    if image_payload.startswith('http://') or image_payload.startswith('https://'):
        actual_ext = infer_extension_from_url(image_payload)
        actual_output = output_path.with_suffix(actual_ext)
        actual_output.write_bytes(download_binary(image_payload))
        return actual_output, 'url'

    if image_payload.startswith('data:'):
        try:
            _, b64 = image_payload.split(',', 1)
        except ValueError as exc:
            raise RuntimeError('Invalid data URL image payload') from exc
        output_path.write_bytes(base64.b64decode(b64))
        return output_path, 'data_url'

    output_path.write_bytes(base64.b64decode(image_payload))
    return output_path, 'b64_json'


def generate_openai_images_api(prompt: str, size: str, model: str, base_url: str, api_key: str, output_path: Path, aspect_ratio: str | None, resolution: str | None) -> dict:
    endpoint = f'{base_url}/images/generations'
    actual_size = normalize_openai_size(size)
    payload = {
        'model': model,
        'prompt': prompt,
        'size': actual_size,
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
    image_payload = first.get('b64_json') or first.get('url')
    if not image_payload:
        raise RuntimeError(f'Unsupported provider response shape: {first}')

    saved_output, source_mode = save_image_result(image_payload, output_path)
    return {
        'status': 'ok',
        'mode': 'openai-compatible-images',
        'prompt': prompt,
        'inputImage': None,
        'output': str(saved_output),
        'requestedSize': size,
        'size': actual_size,
        'aspectRatio': aspect_ratio,
        'resolution': resolution,
        'provider': 'openai-compatible',
        'model': model,
        'baseUrl': base_url,
        'responseSource': source_mode,
    }


def parse_responses_output(payload: dict) -> tuple[str, dict]:
    output = payload.get('output')
    if not isinstance(output, list):
        raise RuntimeError(f'Unsupported responses payload: {payload}')

    for item in output:
        if not isinstance(item, dict):
            continue
        if item.get('type') != 'image_generation_call':
            continue
        result = item.get('result')
        if isinstance(result, str) and result.strip():
            actual = {
                'size': item.get('size'),
                'quality': item.get('quality'),
                'output_format': item.get('output_format'),
                'revised_prompt': item.get('revised_prompt'),
            }
            return result, actual

    raise RuntimeError(f'No image_generation_call result in responses payload: {payload}')


def generate_openai_responses_api(prompt: str, size: str, model: str, base_url: str, api_key: str, output_path: Path, aspect_ratio: str | None, resolution: str | None) -> dict:
    endpoint = f'{base_url}/responses'
    actual_size = normalize_openai_size(size)
    payload = {
        'model': model,
        'input': f'Use the following text as the complete prompt. Do not rewrite it:\n{prompt}',
        'tools': [
            {
                'type': 'image_generation',
                'size': actual_size,
            }
        ],
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }

    data = http_json(endpoint, payload, headers)
    image_payload, actual = parse_responses_output(data)
    saved_output, source_mode = save_image_result(image_payload, output_path)
    return {
        'status': 'ok',
        'mode': 'openai-compatible-responses',
        'prompt': prompt,
        'inputImage': None,
        'output': str(saved_output),
        'requestedSize': size,
        'size': actual.get('size') or actual_size,
        'aspectRatio': aspect_ratio,
        'resolution': resolution,
        'provider': 'openai-compatible',
        'model': model,
        'baseUrl': base_url,
        'responseSource': source_mode,
        'actual': actual,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Nano Banana style image generation bridge skeleton')
    parser.add_argument('--prompt', required=True, help='Text prompt for generation/editing')
    parser.add_argument('--input-image', help='Optional input image path for image-to-image/edit mode')
    parser.add_argument('--size', help='Explicit output size, e.g. 1024x1024 or 2048x1152')
    parser.add_argument('--aspect-ratio', choices=list(ASPECT_RATIO_TO_SIZE.keys()), help='Aspect ratio preset')
    parser.add_argument('--resolution', choices=['1K', '2K', '4K'], help='Resolution tier used with --aspect-ratio')
    parser.add_argument('--provider', default='mock', help='Provider name: mock | openai-compatible')
    parser.add_argument('--api-mode', choices=['images', 'responses', 'auto'], default='auto', help='API style for openai-compatible provider')
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

    try:
        size = resolve_size(args.size, args.aspect_ratio, args.resolution)
    except ValueError as e:
        print(json.dumps({'status': 'error', 'error': str(e)}, ensure_ascii=False, indent=2))
        return 1

    if args.dry_run:
        print(json.dumps({
            'status': 'ok',
            'mode': 'dry-run',
            'prompt': args.prompt,
            'inputImage': input_image,
            'output': str(output_path),
            'requestedSize': size,
            'normalizedOpenAISize': normalize_openai_size(size),
            'aspectRatio': args.aspect_ratio,
            'resolution': args.resolution,
            'provider': args.provider,
            'apiMode': args.api_mode,
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
            'requestedSize': size,
            'size': normalize_openai_size(size),
            'aspectRatio': args.aspect_ratio,
            'resolution': args.resolution,
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
            if args.api_mode == 'images':
                result = generate_openai_images_api(
                    prompt=args.prompt,
                    size=size,
                    model=model,
                    base_url=base_url,
                    api_key=api_key,
                    output_path=output_path,
                    aspect_ratio=args.aspect_ratio,
                    resolution=args.resolution,
                )
            elif args.api_mode == 'responses':
                result = generate_openai_responses_api(
                    prompt=args.prompt,
                    size=size,
                    model=model,
                    base_url=base_url,
                    api_key=api_key,
                    output_path=output_path,
                    aspect_ratio=args.aspect_ratio,
                    resolution=args.resolution,
                )
            else:
                try:
                    result = generate_openai_images_api(
                        prompt=args.prompt,
                        size=size,
                        model=model,
                        base_url=base_url,
                        api_key=api_key,
                        output_path=output_path,
                        aspect_ratio=args.aspect_ratio,
                        resolution=args.resolution,
                    )
                except Exception as first_error:
                    result = generate_openai_responses_api(
                        prompt=args.prompt,
                        size=size,
                        model=model,
                        base_url=base_url,
                        api_key=api_key,
                        output_path=output_path,
                        aspect_ratio=args.aspect_ratio,
                        resolution=args.resolution,
                    )
                    result['fallbackFrom'] = str(first_error)

            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        except urllib.error.HTTPError as e:
            details = e.read().decode('utf-8', errors='replace')
            print(json.dumps({
                'status': 'error',
                'error': f'HTTP {e.code} calling provider',
                'details': details,
                'provider': args.provider,
                'apiMode': args.api_mode,
                'baseUrl': base_url,
                'model': model,
                'requestedSize': size,
                'normalizedOpenAISize': normalize_openai_size(size),
            }, ensure_ascii=False, indent=2))
            return 1
        except Exception as e:
            print(json.dumps({
                'status': 'error',
                'error': str(e),
                'provider': args.provider,
                'apiMode': args.api_mode,
                'baseUrl': base_url,
                'model': model,
                'requestedSize': size,
                'normalizedOpenAISize': normalize_openai_size(size),
            }, ensure_ascii=False, indent=2))
            return 1

    print(json.dumps({
        'status': 'error',
        'error': f'Unsupported provider: {args.provider}'
    }, ensure_ascii=False, indent=2))
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
