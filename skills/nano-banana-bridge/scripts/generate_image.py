import argparse
import json
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / 'output'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_output_path(prefix: str = 'nano-banana') -> Path:
    stamp = time.strftime('%Y%m%d_%H%M%S')
    return OUTPUT_DIR / f'{prefix}_{stamp}.png'


def main() -> int:
    parser = argparse.ArgumentParser(description='Nano Banana style image generation bridge skeleton')
    parser.add_argument('--prompt', required=True, help='Text prompt for generation/editing')
    parser.add_argument('--input-image', help='Optional input image path for image-to-image/edit mode')
    parser.add_argument('--size', default='1024x1024', help='Output size, e.g. 1024x1024 or 1536x1024')
    parser.add_argument('--provider', default='mock', help='Provider name placeholder')
    parser.add_argument('--mock', action='store_true', help='Run in mock mode (default recommended for now)')
    parser.add_argument('--dry-run', action='store_true', help='Only print planned action, do not generate file')
    args = parser.parse_args()

    input_image = str(Path(args.input_image).resolve()) if args.input_image else None
    output_path = build_output_path()

    if args.dry_run:
        print(json.dumps({
            'status': 'ok',
            'mode': 'dry-run',
            'prompt': args.prompt,
            'inputImage': input_image,
            'output': str(output_path),
            'size': args.size,
            'provider': args.provider,
        }, ensure_ascii=False, indent=2))
        return 0

    if args.mock or args.provider == 'mock':
        # 先写一个占位 PNG 文件，方便后续工作流联调
        output_path.write_bytes(b'')
        print(json.dumps({
            'status': 'ok',
            'mode': 'mock',
            'prompt': args.prompt,
            'inputImage': input_image,
            'output': str(output_path),
            'size': args.size,
            'provider': 'mock',
            'note': 'Skeleton only. Replace mock branch with a real provider call later.'
        }, ensure_ascii=False, indent=2))
        return 0

    print(json.dumps({
        'status': 'error',
        'error': 'Real provider not implemented yet. Use --mock or extend this script with a provider integration.'
    }, ensure_ascii=False, indent=2))
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
