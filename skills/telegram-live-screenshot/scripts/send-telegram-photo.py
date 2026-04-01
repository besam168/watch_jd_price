import json
import sys
from pathlib import Path

import requests


def load_openclaw_config():
    config_path = Path(r"C:\Users\besam\.openclaw\openclaw.json")
    return json.loads(config_path.read_text(encoding="utf-8"))


def main():
    if len(sys.argv) < 3:
        print("Usage: python send-telegram-photo.py <image_path> <chat_id> [caption]", file=sys.stderr)
        sys.exit(2)

    image_path = Path(sys.argv[1]).expanduser().resolve()
    chat_id = str(sys.argv[2])
    caption = sys.argv[3] if len(sys.argv) > 3 else ""

    if not image_path.exists():
        print(f"Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    config = load_openclaw_config()
    bot_token = config.get("channels", {}).get("telegram", {}).get("botToken")
    if not bot_token:
        print("Telegram bot token not found in openclaw.json", file=sys.stderr)
        sys.exit(1)

    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    data = {
        "chat_id": chat_id,
    }
    if caption:
        data["caption"] = caption

    with image_path.open("rb") as f:
        files = {
            "photo": (image_path.name, f, "image/png"),
        }
        resp = requests.post(url, data=data, files=files, timeout=60)

    if not resp.ok:
        print(resp.text, file=sys.stderr)
        sys.exit(1)

    payload = resp.json()
    if not payload.get("ok"):
        print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    result = payload.get("result", {})
    print(json.dumps({
        "ok": True,
        "message_id": result.get("message_id"),
        "chat_id": result.get("chat", {}).get("id"),
        "photo_count": len(result.get("photo", [])),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
