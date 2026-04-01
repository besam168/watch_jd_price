from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from uuid import uuid4

from scripts import bridge_server
from scripts.speak import load_config, speak


class MvpSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        tests_tmp_root = Path(__file__).resolve().parents[1] / ".tmp_tests"
        tests_tmp_root.mkdir(parents=True, exist_ok=True)
        self._tmpdir = tests_tmp_root / f"tmall_bridge_test_{uuid4().hex[:12]}"
        self._tmpdir.mkdir(parents=True, exist_ok=True)
        self.config_path = self._tmpdir / "config.json"
        self.audio_dir = self._tmpdir / "tmp_audio"

        config = {
            "host": "127.0.0.1",
            "port": 57881,
            "tts": {
                "provider": "mock",
                "voice": "zh-CN-XiaoxiaoNeural",
                "rate": "+0%",
                "output_dir": "./tmp_audio",
                "output_ext": "wav",
                "max_text_length": 128,
            },
            "backend": {
                "type": "mock_tmall_genie",
                "options": {
                    "device_name": "test-device",
                    "device_ip": "127.0.0.1",
                },
            },
            "http_player": {
                "audio_base_url": "auto",
            },
        }
        self.config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

        bridge_server.APP_CONFIG_PATH = self.config_path
        bridge_server.APP_CONFIG = load_config(self.config_path)
        bridge_server.app.testing = True
        self.client = bridge_server.app.test_client()

    def tearDown(self) -> None:
        bridge_server.APP_CONFIG = {}
        bridge_server.APP_CONFIG_PATH = None
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_speak_function_generates_audio_file(self) -> None:
        result = speak(
            text="smoke test",
            config=bridge_server.APP_CONFIG,
            config_path=self.config_path,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["backend"], "mock_tmall_genie")
        self.assertTrue(Path(result["audio_path"]).exists())

    def test_speak_endpoint_accepts_plain_text_body(self) -> None:
        response = self.client.post("/speak", data="plain text request", content_type="text/plain")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        assert payload is not None
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["text"], "plain text request")

    def test_speak_endpoint_honors_forwarded_headers_for_auto_audio_url(self) -> None:
        response = self.client.post(
            "/speak",
            json={"text": "forwarded host test"},
            headers={
                "X-Forwarded-Proto": "https",
                "X-Forwarded-Host": "bridge.example.com",
                "X-Forwarded-Prefix": "/bridge",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        assert payload is not None
        self.assertTrue(payload["audio_url"].startswith("https://bridge.example.com/bridge/audio/"))

    def test_callback_endpoint_accepts_form_dotted_keys(self) -> None:
        response = self.client.post(
            "/callback/text",
            data={
                "payload.query": "from dotted form",
                "source": "form-test",
                "session_id": "session-1",
            },
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        assert payload is not None
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["recognized_text"], "from dotted form")
        self.assertEqual(payload["callback"]["source"], "form-test")

    def test_audio_endpoint_serves_generated_file(self) -> None:
        generated = speak(
            text="audio endpoint smoke",
            config=bridge_server.APP_CONFIG,
            config_path=self.config_path,
        )
        audio_name = Path(generated["audio_path"]).name
        response = self.client.get(f"/audio/{audio_name}")
        try:
            self.assertEqual(response.status_code, 200)
            self.assertGreater(len(response.data), 0)
        finally:
            response.close()

    def test_speak_rejects_overlong_input(self) -> None:
        response = self.client.post("/speak", json={"text": "x" * 129})
        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        assert payload is not None
        self.assertIn("too long", payload["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
