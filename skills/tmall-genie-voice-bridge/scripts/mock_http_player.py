from __future__ import annotations

import argparse
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict


class MockHttpPlayerHandler(BaseHTTPRequestHandler):
    server_version = "TmallGenieMockHttpPlayer/0.1"

    def _json_response(self, status: int, payload: Dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/health":
            self._json_response(200, {"ok": True, "service": "mock_http_player"})
            return
        self._json_response(404, {"ok": False, "error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        raw_body = self.rfile.read(length) if length > 0 else b""

        try:
            payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except json.JSONDecodeError:
            self._json_response(400, {"ok": False, "error": "Invalid JSON body"})
            return

        record = {
            "received_at": datetime.now().isoformat(timespec="seconds"),
            "method": "POST",
            "path": self.path,
            "headers": {k: v for k, v in self.headers.items()},
            "payload": payload,
        }
        self.server.last_request = record  # type: ignore[attr-defined]

        output_path: Path | None = getattr(self.server, "output_path", None)  # type: ignore[attr-defined]
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

        self._json_response(
            200,
            {
                "ok": True,
                "service": "mock_http_player",
                "received": True,
                "path": self.path,
                "payload": payload,
            },
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Mock HTTP player receiver for tmall-genie-voice-bridge demos.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=58081)
    parser.add_argument("--output", default="", help="Optional path to save the last received request as JSON")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), MockHttpPlayerHandler)
    server.output_path = Path(args.output).resolve() if args.output else None  # type: ignore[attr-defined]
    server.last_request = None  # type: ignore[attr-defined]

    print(json.dumps({
        "ok": True,
        "service": "mock_http_player",
        "listen": f"http://{args.host}:{args.port}",
        "output": str(server.output_path) if server.output_path else None,
    }, ensure_ascii=False))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
