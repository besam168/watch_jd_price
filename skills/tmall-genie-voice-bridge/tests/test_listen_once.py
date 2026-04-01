from __future__ import annotations

import base64
import json
import unittest
from pathlib import Path
from unittest import mock

from scripts import listen_once as listen_once_module


class DecodePowerShellJsonTests(unittest.TestCase):
    def test_decode_accepts_base64_last_line(self) -> None:
        payload = {"ok": True, "text": "你好"}
        encoded = base64.b64encode(json.dumps(payload, ensure_ascii=False).encode("utf-8")).decode("ascii")

        result = listen_once_module._decode_powershell_json(f"noise\n{encoded}\n")

        self.assertEqual(result, payload)

    def test_decode_accepts_plain_json_last_line(self) -> None:
        payload = {"ok": True, "text": "plain"}

        result = listen_once_module._decode_powershell_json(f"debug line\n{json.dumps(payload)}")

        self.assertEqual(result, payload)


class ListenOnceTests(unittest.TestCase):
    def test_microphone_retries_choose_best_confidence_and_keep_attempts(self) -> None:
        responses = [
            {"ok": True, "text": "第一次", "confidence": 0.31, "culture": "zh-CN", "timed_out": False},
            {"ok": True, "text": "第二次", "confidence": 0.92, "culture": "zh-CN", "timed_out": False},
        ]

        with mock.patch.object(listen_once_module, "_powershell_recognize", side_effect=responses):
            result = listen_once_module.listen_once(
                timeout_seconds=8,
                culture="zh-CN",
                wav_path=None,
                attempts=2,
                fallback_wav=None,
                initial_silence_seconds=3.0,
                babble_timeout_seconds=2.0,
                end_silence_seconds=0.8,
                allow_culture_fallback=False,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["text"], "第一次")
        self.assertEqual(result["attempt_count"], 1)
        self.assertNotIn("attempts", result)
        self.assertEqual(result["result_source"], "primary")
        self.assertIn("engine", result)

    def test_microphone_uses_fallback_wav_after_failed_attempts(self) -> None:
        primary_fail_1 = {
            "ok": False,
            "text": "",
            "confidence": None,
            "culture": "zh-CN",
            "timed_out": True,
            "error": "timeout",
        }
        primary_fail_2 = {
            "ok": False,
            "text": "",
            "confidence": None,
            "culture": "zh-CN",
            "timed_out": False,
            "error": "no speech",
        }
        fallback_success = {
            "ok": True,
            "text": "来自回退 WAV",
            "confidence": 0.77,
            "culture": "zh-CN",
            "timed_out": False,
            "wav_path": str(Path("fallback.wav")),
        }

        with mock.patch.object(
            listen_once_module,
            "_powershell_recognize",
            side_effect=[primary_fail_1, primary_fail_2, fallback_success],
        ) as recognize_mock:
            result = listen_once_module.listen_once(
                timeout_seconds=8,
                culture="zh-CN",
                wav_path=None,
                attempts=2,
                fallback_wav=Path("fallback.wav"),
                initial_silence_seconds=3.0,
                babble_timeout_seconds=2.0,
                end_silence_seconds=0.8,
                allow_culture_fallback=False,
            )

        self.assertEqual(recognize_mock.call_count, 3)
        self.assertTrue(result["ok"])
        self.assertEqual(result["text"], "来自回退 WAV")
        self.assertEqual(result["result_source"], "fallback_wav")
        self.assertEqual(result["attempt_count"], 2)
        self.assertEqual(len(result["attempts"]), 2)
        self.assertIn("fallback", result)
        self.assertTrue(any("timed out" in warning for warning in result["warnings"]))
        self.assertTrue(any("--fallback-wav" in warning for warning in result["warnings"]))

    def test_wav_mode_runs_once_and_sets_wav_path_when_missing(self) -> None:
        wav_path = Path("sample.wav").resolve()
        with mock.patch.object(
            listen_once_module,
            "_powershell_recognize",
            return_value={"ok": True, "text": "wav text", "confidence": 0.5, "culture": "zh-CN"},
        ) as recognize_mock:
            result = listen_once_module.listen_once(
                timeout_seconds=8,
                culture="zh-CN",
                wav_path=wav_path,
                attempts=5,
                fallback_wav=None,
                initial_silence_seconds=3.0,
                babble_timeout_seconds=2.0,
                end_silence_seconds=0.8,
                allow_culture_fallback=False,
            )

        self.assertEqual(recognize_mock.call_count, 1)
        self.assertEqual(result["mode"], "wav_file")
        self.assertEqual(result["attempt_count"], 1)
        self.assertEqual(result["wav_path"], str(wav_path))
        self.assertNotIn("attempts", result)

    def test_build_warnings_includes_culture_fallback_notice(self) -> None:
        warnings = listen_once_module._build_warnings(
            result={
                "ok": False,
                "culture_fallback_used": True,
                "selected_culture": "en-US",
                "requested_culture": "zh-CN",
                "timed_out": False,
                "result_source": "primary",
            },
            timeout_seconds=8,
            primary_mode="microphone",
            fallback_wav=None,
        )

        self.assertTrue(any("fell back to 'en-US'" in warning for warning in warnings))
        self.assertTrue(any("deterministic --wav path" in warning for warning in warnings))


if __name__ == "__main__":
    unittest.main(verbosity=2)
