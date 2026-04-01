from __future__ import annotations

import argparse
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict


class MockHttpPlayerHandler(BaseHTTPRequestHandler):
    server_version = "TmallGenieMockHttpPlayer/0.2"

    def _json_response(self, status: int, payload: Dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/health":
            self._json_response(
                200,
                {
                    "ok": True,
                    "service": "mock_http_player",
                    "require_auth": bool(getattr(self.server, "required_bearer", "")),
                    "required_entity_id": getattr(self.server, "required_entity_id", "") or None,
                    "forced_status": getattr(self.server, "forced_status", 200),
                },
            )
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

        required_bearer = str(getattr(self.server, "required_bearer", "") or "")  # type: ignore[attr-defined]
        if required_bearer:
            auth = self.headers.get("Authorization", "")
            if auth != f"Bearer {required_bearer}":
                self._json_response(401, {"ok": False, "error": "Unauthorized", "detail": "Bearer token mismatch"})
                return

        required_entity_id = str(getattr(self.server, "required_entity_id", "") or "")  # type: ignore[attr-defined]
        if required_entity_id:
            actual_entity_id = str(payload.get("entity_id") or "")
            if actual_entity_id != required_entity_id:
                self._json_response(
                    422,
                    {
                        "ok": False,
                        "error": "Entity mismatch",
                        "expected_entity_id": required_entity_id,
                        "actual_entity_id": actual_entity_id,
                    },
                )
                return

        forced_status = int(getattr(self.server, "forced_status", 200) or 200)  # type: ignore[attr-defined]
        if forced_status != 200:
            self._json_response(
                forced_status,
                {
                    "ok": False,
                    "service": "mock_http_player",
                    "received": True,
                    "path": self.path,
                    "payload": payload,
                    "error": f"Forced status {forced_status}",
                },
            )
            return

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
    parser.add_argument("--require-bearer", default="", help="If set, require Authorization: Bearer <token>")
    parser.add_argument("--require-entity-id", default="", help="If set, require payload.entity_id to match")
    parser.add_argument("--forced-status", type=int, default=200, help="If not 200, always return this status after validation")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), MockHttpPlayerHandler)
    server.output_path = Path(args.output).resolve() if args.output else None  # type: ignore[attr-defined]
    server.last_request = None  # type: ignore[attr-defined]
    server.required_bearer = args.require_bearer  # type: ignore[attr-defined]
    server.required_entity_id = args.require_entity_id  # type: ignore[attr-defined]
    server.forced_status = args.forced_status  # type: ignore[attr-defined]

    print(json.dumps({
        "ok": True,
        "service": "mock_http_player",
        "listen": f"http://{args.host}:{args.port}",
        "output": str(server.output_path) if server.output_path else None,
        "require_auth": bool(args.require_bearer),
        "required_entity_id": args.require_entity_id or None,
        "forced_status": args.forced_status,
    }, ensure_ascii=False))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
