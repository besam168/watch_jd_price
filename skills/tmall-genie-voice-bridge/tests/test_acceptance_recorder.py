from __future__ import annotations

import json
import shutil
import unittest
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from scripts.record_acceptance_result import (
    PROJECT_ROOT,
    JsonInput,
    build_acceptance_record,
    record_acceptance_result,
    write_acceptance_record,
)


class AcceptanceRecorderTests(unittest.TestCase):
    def setUp(self) -> None:
        tests_tmp_root = Path(__file__).resolve().parents[1] / ".tmp_tests"
        tests_tmp_root.mkdir(parents=True, exist_ok=True)
        self._tmpdir = tests_tmp_root / f"tmall_bridge_acceptance_{uuid4().hex[:12]}"
        self._tmpdir.mkdir(parents=True, exist_ok=True)

        self.config_path = self._tmpdir / "config.json"
        self.preflight_path = self._tmpdir / "preflight.json"
        self.rehearsal_path = self._tmpdir / "rehearsal.json"

        self.config_path.write_text(
            json.dumps(
                {
                    "backend": {"type": "local_http_player"},
                    "http_player": {"player_url": "http://player.local/play"},
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        self.preflight_path.write_text(
            json.dumps({"ok": True, "issues": [], "warnings": []}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.rehearsal_path.write_text(
            json.dumps(
                {"ok": True, "request": {"http_status": 200, "target_status": 200}},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_recorder_writes_json_and_markdown_from_paths(self) -> None:
        out_dir = self._tmpdir / "records"
        result = record_acceptance_result(
            config_path=str(self.config_path),
            preflight_json_path=str(self.preflight_path),
            preflight_json_inline=None,
            rehearsal_json_path=str(self.rehearsal_path),
            rehearsal_json_inline=None,
            human_heard=True,
            human_note="Audio heard from living room speaker.",
            output_dir=str(out_dir),
            output_format="both",
        )

        self.assertTrue(result["ok"])
        self.assertTrue(Path(result["record_json"]).exists())
        self.assertTrue(Path(result["record_markdown"]).exists())
        self.assertEqual(result["record"]["preflight"]["source"], "path")
        self.assertEqual(result["record"]["rehearsal"]["source"], "path")
        self.assertTrue(result["record"]["summary"]["hardware_playback_verified"])
        self.assertEqual(Path(result["output_dir"]).resolve(), out_dir.resolve())
        self.assertEqual(len(result["files_written"]), 2)

    def test_recorder_accepts_inline_json_inputs(self) -> None:
        out_dir = self._tmpdir / "inline-records"
        result = record_acceptance_result(
            config_path=str(self.config_path),
            preflight_json_path=None,
            preflight_json_inline='{"ok": false, "issues": ["token placeholder"]}',
            rehearsal_json_path=None,
            rehearsal_json_inline='{"ok": false, "request": {"target_status": 401}}',
            human_heard=False,
            human_note="No playback expected in this run.",
            output_dir=str(out_dir),
            output_format="json",
        )

        self.assertTrue(result["ok"])
        self.assertIsNotNone(result["record_json"])
        self.assertIsNone(result["record_markdown"])
        self.assertEqual(result["record"]["preflight"]["source"], "inline")
        self.assertEqual(result["record"]["rehearsal"]["source"], "inline")
        self.assertEqual(result["record"]["summary"]["target_status"], 401)
        self.assertFalse(result["record"]["summary"]["hardware_playback_verified"])

    def test_mutually_exclusive_json_inputs_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            record_acceptance_result(
                config_path=str(self.config_path),
                preflight_json_path=str(self.preflight_path),
                preflight_json_inline='{"ok": true}',
                rehearsal_json_path=None,
                rehearsal_json_inline=None,
                human_heard=False,
                human_note="",
                output_dir=str(self._tmpdir / "records"),
                output_format="json",
            )

    def test_empty_note_is_normalized_when_human_heard(self) -> None:
        out_dir = self._tmpdir / "normalized-note"
        result = record_acceptance_result(
            config_path=str(self.config_path),
            preflight_json_path=str(self.preflight_path),
            preflight_json_inline=None,
            rehearsal_json_path=str(self.rehearsal_path),
            rehearsal_json_inline=None,
            human_heard=True,
            human_note="   ",
            output_dir=str(out_dir),
            output_format="json",
        )

        self.assertEqual(
            result["record"]["human_confirmation"]["note"],
            "Human heard playback (no additional note provided).",
        )

    def test_write_record_uses_unique_name_on_collision(self) -> None:
        out_dir = self._tmpdir / "collision-records"
        out_dir.mkdir(parents=True, exist_ok=True)
        created_at = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc)
        record = build_acceptance_record(
            config_path=self.config_path,
            preflight=JsonInput(source="path", path=str(self.preflight_path), data={"ok": True}),
            rehearsal=JsonInput(source="path", path=str(self.rehearsal_path), data={"ok": True}),
            human_heard=False,
            human_note="collision test",
            created_at=created_at,
        )

        first_json, first_md = write_acceptance_record(record=record, output_dir=out_dir, output_format="both")
        second_json, second_md = write_acceptance_record(record=record, output_dir=out_dir, output_format="both")

        self.assertIsNotNone(first_json)
        self.assertIsNotNone(second_json)
        self.assertIsNotNone(first_md)
        self.assertIsNotNone(second_md)
        self.assertNotEqual(first_json, second_json)
        self.assertNotEqual(first_md, second_md)
        self.assertTrue(first_json.exists())
        self.assertTrue(second_json.exists())
        self.assertTrue(first_md.exists())
        self.assertTrue(second_md.exists())

    def test_output_dir_must_stay_inside_repo(self) -> None:
        outside_dir = PROJECT_ROOT.parent / "outside-acceptance-output"
        with self.assertRaises(ValueError):
            record_acceptance_result(
                config_path=str(self.config_path),
                preflight_json_path=None,
                preflight_json_inline=None,
                rehearsal_json_path=None,
                rehearsal_json_inline=None,
                human_heard=False,
                human_note="",
                output_dir=str(outside_dir),
                output_format="json",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
