from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from unittest import mock
from uuid import uuid4

from scripts import bridge_server
from scripts.preflight_real_http_player import evaluate_config
from scripts.rehearse_real_http_player import run_rehearsal
from scripts.speak import load_config, speak
from scripts.backends.local_http_player import PlaybackTargetHttpError


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

    def test_public_base_url_overrides_forwarded_headers(self) -> None:
        bridge_server.APP_CONFIG["http_player"] = {
            "audio_base_url": "auto",
            "public_base_url": "https://public.example.com/bridge-root",
        }
        response = self.client.post(
            "/speak",
            json={"text": "public base url test"},
            headers={
                "X-Forwarded-Proto": "https",
                "X-Forwarded-Host": "ignored.example.com",
                "X-Forwarded-Prefix": "/ignored",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        assert payload is not None
        self.assertTrue(
            payload["audio_url"].startswith("https://public.example.com/bridge-root/audio/")
        )

    def test_local_http_player_receives_rendered_payload(self) -> None:
        http_config = json.loads(json.dumps(bridge_server.APP_CONFIG))
        http_config["backend"] = {
            "type": "local_http_player",
            "options": {},
        }
        http_config["http_player"] = {
            "player_url": "http://player.local/play",
            "method": "POST",
            "timeout": 9,
            "headers": {
                "Authorization": "Bearer test-token",
            },
            "body_template": {
                "entity_id": "media_player.test_speaker",
                "media_content_id": "{{audio_url}}",
                "media_content_type": "music",
                "meta": {
                    "spoken_text": "{{text}}",
                    "local_file": "{{audio_path}}",
                },
            },
            "public_base_url": "https://public.example.com/bridge",
        }

        with mock.patch("scripts.backends.local_http_player.requests.request") as request_mock:
            response_mock = mock.Mock()
            response_mock.status_code = 200
            response_mock.text = '{"ok":true}'
            response_mock.raise_for_status.return_value = None
            request_mock.return_value = response_mock

            result = speak(
                text="play through http backend",
                config=http_config,
                config_path=self.config_path,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["backend"], "local_http_player")
        self.assertTrue(result["audio_url"].startswith("https://public.example.com/bridge/"))

        _, kwargs = request_mock.call_args
        self.assertEqual(kwargs["method"], "POST")
        self.assertEqual(kwargs["url"], "http://player.local/play")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-token")
        self.assertEqual(kwargs["timeout"], 9)
        self.assertEqual(kwargs["json"]["entity_id"], "media_player.test_speaker")
        self.assertEqual(kwargs["json"]["media_content_id"], result["audio_url"])
        self.assertEqual(kwargs["json"]["meta"]["spoken_text"], "play through http backend")
        self.assertEqual(kwargs["json"]["meta"]["local_file"], result["audio_path"])

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

    def test_speak_route_surfaces_target_401(self) -> None:
        with mock.patch("scripts.bridge_server.speak") as speak_mock:
            speak_mock.side_effect = PlaybackTargetHttpError(
                status_code=401,
                player_url="http://player.local/play",
                response_text='{"ok":false,"error":"Unauthorized"}',
                payload={"entity_id": "media_player.test"},
            )
            response = self.client.post("/speak", json={"text": "auth fail test"})

        self.assertEqual(response.status_code, 401)
        payload = response.get_json()
        assert payload is not None
        self.assertEqual(payload["target_status"], 401)
        self.assertEqual(payload["player_url"], "http://player.local/play")
        self.assertIn("Unauthorized", payload["target_response_preview"])

    def test_speak_route_surfaces_target_422(self) -> None:
        with mock.patch("scripts.bridge_server.speak") as speak_mock:
            speak_mock.side_effect = PlaybackTargetHttpError(
                status_code=422,
                player_url="http://player.local/play",
                response_text='{"ok":false,"error":"Entity mismatch"}',
                payload={"entity_id": "media_player.actual"},
            )
            response = self.client.post("/speak", json={"text": "entity fail test"})

        self.assertEqual(response.status_code, 422)
        payload = response.get_json()
        assert payload is not None
        self.assertEqual(payload["target_status"], 422)
        self.assertIn("Entity mismatch", payload["target_response_preview"])

    def test_callback_route_surfaces_target_500(self) -> None:
        with mock.patch("scripts.bridge_server.speak") as speak_mock:
            speak_mock.side_effect = PlaybackTargetHttpError(
                status_code=500,
                player_url="http://player.local/play",
                response_text='{"ok":false,"error":"Forced status 500"}',
                payload={"entity_id": "media_player.test"},
            )
            response = self.client.post("/callback/text", json={"query": "server fail test", "source": "matrix"})

        self.assertEqual(response.status_code, 500)
        payload = response.get_json()
        assert payload is not None
        self.assertEqual(payload["target_status"], 500)
        self.assertEqual(payload["callback"]["source"], "matrix")
        self.assertIn("Forced status 500", payload["target_response_preview"])


class RealHttpPlayerRehearsalTests(unittest.TestCase):
    def setUp(self) -> None:
        tests_tmp_root = Path(__file__).resolve().parents[1] / ".tmp_tests"
        tests_tmp_root.mkdir(parents=True, exist_ok=True)
        self._tmpdir = tests_tmp_root / f"tmall_bridge_rehearsal_{uuid4().hex[:12]}"
        self._tmpdir.mkdir(parents=True, exist_ok=True)
        self.config_path = self._tmpdir / "config.json"
        self.config_path.write_text(
            json.dumps(
                {
                    "host": "127.0.0.1",
                    "port": 57881,
                    "tts": {
                        "provider": "mock",
                        "output_dir": "./tmp_audio",
                        "output_ext": "wav",
                        "max_text_length": 128,
                    },
                    "backend": {
                        "type": "local_http_player",
                        "options": {},
                    },
                    "http_player": {
                        "player_url": "http://player.local/play",
                        "headers": {
                            "Authorization": "Bearer real-token",
                        },
                        "body_template": {
                            "entity_id": "media_player.real_speaker",
                            "media_content_id": "{{audio_url}}",
                            "media_content_type": "music",
                        },
                        "public_base_url": "https://bridge.example.com",
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_rehearsal_stops_when_preflight_fails(self) -> None:
        self.config_path.write_text(
            json.dumps(
                {
                    "backend": {"type": "mock_tmall_genie"},
                    "http_player": {
                        "player_url": "http://HOME_ASSISTANT_HOST:8123/api/services/media_player/play_media",
                        "headers": {"Authorization": "Bearer REPLACE_WITH_REAL_TOKEN"},
                        "body_template": {"entity_id": "media_player.REPLACE_ME"},
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        with mock.patch("scripts.rehearse_real_http_player.requests.post") as post_mock:
            result = run_rehearsal(
                config_path=self.config_path,
                bridge_url="http://127.0.0.1:57881/speak",
                text="should not send",
                skip_probe=True,
            )

        self.assertFalse(result["ok"])
        self.assertFalse(result["preflight"]["ok"])
        self.assertTrue(result["request"]["skipped"])
        post_mock.assert_not_called()

    def test_rehearsal_returns_structured_summary_on_bridge_error(self) -> None:
        response_mock = mock.Mock()
        response_mock.ok = False
        response_mock.status_code = 401
        response_mock.json.return_value = {
            "ok": False,
            "error": "Unauthorized",
            "target_status": 401,
            "player_url": "http://player.local/play",
        }

        with mock.patch("scripts.rehearse_real_http_player.requests.post", return_value=response_mock) as post_mock:
            result = run_rehearsal(
                config_path=self.config_path,
                bridge_url="http://127.0.0.1:57881/speak",
                text="auth fail demo",
                skip_probe=True,
            )

        self.assertFalse(result["ok"])
        self.assertTrue(result["preflight"]["ok"])
        self.assertEqual(result["request"]["http_status"], 401)
        self.assertEqual(result["request"]["target_status"], 401)
        self.assertEqual(result["request"]["player_url"], "http://player.local/play")
        post_mock.assert_called_once()

    def test_rehearsal_returns_audio_url_on_success(self) -> None:
        response_mock = mock.Mock()
        response_mock.ok = True
        response_mock.status_code = 200
        response_mock.json.return_value = {
            "ok": True,
            "backend": "local_http_player",
            "audio_url": "https://bridge.example.com/audio/demo.mp3",
        }

        with mock.patch("scripts.rehearse_real_http_player.requests.post", return_value=response_mock):
            result = run_rehearsal(
                config_path=self.config_path,
                bridge_url="http://127.0.0.1:57881/speak",
                text="success demo",
                skip_probe=True,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["request"]["backend"], "local_http_player")
        self.assertEqual(result["request"]["audio_url"], "https://bridge.example.com/audio/demo.mp3")


class MockHttpPlayerHandlerTests(unittest.TestCase):
    def _start_server(self, *, required_bearer: str = "", required_entity_id: str = "", forced_status: int = 200):
        from scripts.mock_http_player import MockHttpPlayerHandler
        from http.server import ThreadingHTTPServer
        import threading

        server = ThreadingHTTPServer(("127.0.0.1", 0), MockHttpPlayerHandler)
        server.output_path = None  # type: ignore[attr-defined]
        server.last_request = None  # type: ignore[attr-defined]
        server.required_bearer = required_bearer  # type: ignore[attr-defined]
        server.required_entity_id = required_entity_id  # type: ignore[attr-defined]
        server.forced_status = forced_status  # type: ignore[attr-defined]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread

    def test_mock_http_player_health_and_post(self) -> None:
        import requests

        server, thread = self._start_server()
        try:
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            health = requests.get(base_url + "/health", timeout=5)
            self.assertEqual(health.status_code, 200)
            self.assertTrue(health.json()["ok"])

            payload = {"media_content_id": "https://example.com/audio/demo.mp3", "entity_id": "media_player.test"}
            response = requests.post(base_url + "/play", json=payload, timeout=5)
            self.assertEqual(response.status_code, 200)
            body = response.json()
            self.assertTrue(body["ok"])
            self.assertEqual(body["payload"]["entity_id"], "media_player.test")
            self.assertEqual(server.last_request["payload"]["media_content_id"], payload["media_content_id"])  # type: ignore[index]
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_mock_http_player_rejects_missing_bearer(self) -> None:
        import requests

        server, thread = self._start_server(required_bearer="secret-token")
        try:
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            response = requests.post(base_url + "/play", json={"entity_id": "media_player.test"}, timeout=5)
            self.assertEqual(response.status_code, 401)
            self.assertIn("Unauthorized", response.text)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_mock_http_player_rejects_wrong_entity_id(self) -> None:
        import requests

        server, thread = self._start_server(required_entity_id="media_player.expected")
        try:
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            response = requests.post(
                base_url + "/play",
                json={"entity_id": "media_player.actual", "media_content_id": "https://example.com/audio.mp3"},
                timeout=5,
            )
            self.assertEqual(response.status_code, 422)
            body = response.json()
            self.assertEqual(body["expected_entity_id"], "media_player.expected")
            self.assertEqual(body["actual_entity_id"], "media_player.actual")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_mock_http_player_can_force_server_error(self) -> None:
        import requests

        server, thread = self._start_server(forced_status=500)
        try:
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            response = requests.post(base_url + "/play", json={"entity_id": "media_player.test"}, timeout=5)
            self.assertEqual(response.status_code, 500)
            self.assertIn("Forced status 500", response.text)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
