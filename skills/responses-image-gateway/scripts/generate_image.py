import argparse
import base64
import json
from pathlib import Path
from urllib.request import Request, urlopen


def extract_from_completed_obj(obj):
    output = obj.get("output") or []
    for item in output:
        if isinstance(item, dict):
            if item.get("type") == "image_generation_call" and item.get("result"):
                return item["result"]
            result = item.get("result")
            if isinstance(result, str) and result:
                return result
    data = obj.get("data")
    if isinstance(data, str) and data:
        return data
    return None


def extract_image_b64(text):
    text = text.strip()
    if not text:
        return None

    # plain JSON
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            direct = extract_from_completed_obj(obj)
            if direct:
                return direct
    except Exception:
        pass

    # SSE
    completed_obj = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if not payload or payload == "[DONE]":
            continue
        try:
            evt = json.loads(payload)
        except Exception:
            continue
        if evt.get("type") == "response.completed":
            completed_obj = evt.get("response") or evt
            break

    if completed_obj:
        return extract_from_completed_obj(completed_obj)

    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--token", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--model", default="gpt-5.4")
    ap.add_argument("--output", default="output.png")
    args = ap.parse_args()

    body = {
        "model": args.model,
        "tools": [{"type": "image_generation"}],
        "input": args.prompt,
    }

    req = Request(
        args.url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {args.token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        method="POST",
    )

    with urlopen(req, timeout=120) as resp:
        text = resp.read().decode("utf-8", errors="replace")

    image_b64 = extract_image_b64(text)
    if not image_b64:
        raise SystemExit("No image_generation_call.result found in response")

    output_path = Path(args.output).resolve()
    output_path.write_bytes(base64.b64decode(image_b64))
    print("IMAGE_GENERATED")
    print(str(output_path))


if __name__ == "__main__":
    main()
