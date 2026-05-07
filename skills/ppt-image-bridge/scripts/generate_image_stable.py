import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime

ALLOWED_SIZES = {"1024x1024", "1536x1024", "1024x1536", "2048x1152"}
SIZE_ALIASES = {
    "1k-square": "1024x1024",
    "1k-landscape": "1536x1024",
    "1k-portrait": "1024x1536",
    "2k-landscape": "2048x1152",
    "16:9+2k": "2048x1152",
    "2048*1152": "2048x1152",
}


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def print_json(obj: dict) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def fail(error_code: str, message: str, **extra) -> None:
    payload = {
        "status": "error",
        "errorCode": error_code,
        "error": message,
        **extra,
    }
    print_json(payload)
    sys.exit(1)


def normalize_size(size_value: str) -> str:
    raw = (size_value or "").strip()
    lowered = raw.lower().replace(" ", "")
    normalized = SIZE_ALIASES.get(lowered, lowered)
    if normalized not in ALLOWED_SIZES:
        fail(
            "UNSUPPORTED_SIZE",
            f"Unsupported size: {raw}",
            allowedSizes=sorted(ALLOWED_SIZES),
            requestedSize=raw,
        )
    return normalized


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stable OpenAI-compatible image generation bridge")
    parser.add_argument("--prompt", required=True, help="Image prompt")
    parser.add_argument("--provider", default="openai-compatible")
    parser.add_argument("--base-url", default=os.getenv("OPENAI_IMAGE_BASE_URL", ""))
    parser.add_argument("--api-key", default=os.getenv("OPENAI_IMAGE_API_KEY", ""))
    parser.add_argument("--model", default=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2"))
    parser.add_argument("--size", required=True, help="Image size, e.g. 1024x1024 / 1536x1024 / 1024x1536 / 2048x1152")
    parser.add_argument("--output", default="")
    parser.add_argument("--quality", default="high")
    parser.add_argument("--timeout", type=int, default=120)
    return parser.parse_args()


def build_output_path(output_arg: str, base_dir: str) -> str:
    if output_arg:
        return output_arg
    ensure_dir(base_dir)
    return os.path.join(base_dir, f"stable-image_{timestamp()}.png")


def post_json(url: str, api_key: str, payload: dict, timeout: int) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            raw = e.read().decode("utf-8", errors="replace")
        except Exception:
            raw = str(e)
        fail(
            "HTTP_ERROR",
            f"HTTP {e.code}",
            details=raw,
        )
    except urllib.error.URLError as e:
        fail("NETWORK_ERROR", str(e.reason))
    except UnicodeEncodeError as e:
        fail("ENCODING_ERROR", str(e))
    except json.JSONDecodeError as e:
        fail("BAD_JSON", f"Failed to decode JSON response: {e}")
    except Exception as e:
        fail("UNKNOWN_ERROR", str(e))


def save_b64_image(data: dict, output_path: str) -> None:
    items = data.get("data")
    if not isinstance(items, list) or not items:
        fail("BAD_RESPONSE", "Missing data array in response", response=data)

    first = items[0]
    b64_value = first.get("b64_json")
    if not b64_value:
        fail("BAD_RESPONSE", "Response missing b64_json", response=data)

    try:
        image_bytes = base64.b64decode(b64_value)
    except Exception as e:
        fail("DECODE_ERROR", f"Failed to decode image base64: {e}")

    ensure_dir(os.path.dirname(output_path) or ".")
    with open(output_path, "wb") as f:
        f.write(image_bytes)


def main() -> None:
    args = parse_args()

    if args.provider != "openai-compatible":
        fail("UNSUPPORTED_PROVIDER", f"Unsupported provider: {args.provider}")

    if not args.base_url:
        fail("MISSING_BASE_URL", "Missing --base-url or OPENAI_IMAGE_BASE_URL")

    if not args.api_key:
        fail("MISSING_API_KEY", "Missing --api-key or OPENAI_IMAGE_API_KEY")

    prompt = str(args.prompt)
    normalized_size = normalize_size(args.size)
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
    output_path = build_output_path(args.output, output_dir)

    base_url = args.base_url.rstrip("/")
    url = f"{base_url}/images/generations"

    payload = {
        "model": args.model,
        "prompt": prompt,
        "n": 1,
        "size": normalized_size,
        "quality": args.quality,
        "response_format": "b64_json",
    }

    response_json = post_json(url, args.api_key, payload, args.timeout)
    save_b64_image(response_json, output_path)

    print_json(
        {
            "status": "success",
            "provider": args.provider,
            "model": args.model,
            "baseUrl": base_url,
            "requestedSize": args.size,
            "size": normalized_size,
            "responseFormat": "b64_json",
            "output": output_path,
        }
    )


if __name__ == "__main__":
    main()
