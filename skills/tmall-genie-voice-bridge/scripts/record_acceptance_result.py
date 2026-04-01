from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class JsonInput:
    source: str
    path: Optional[str]
    data: Optional[Dict[str, Any]]


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _read_json_file(path: Path, *, field_name: str) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"{field_name} file not found: {path}")
    raw = path.read_text(encoding="utf-8-sig")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} file is not valid JSON: {path}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return parsed


def _read_json_inline(raw: str, *, field_name: str) -> Dict[str, Any]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} inline data is not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{field_name} inline data must be a JSON object")
    return parsed


def _load_optional_json_input(
    *,
    field_name: str,
    file_path: Optional[str],
    inline_json: Optional[str],
) -> JsonInput:
    if file_path and inline_json:
        raise ValueError(f"Use only one of --{field_name}-json-path or --{field_name}-json-inline")

    if not file_path and not inline_json:
        return JsonInput(source="not_provided", path=None, data=None)

    if file_path:
        resolved = Path(file_path).resolve()
        return JsonInput(
            source="path",
            path=str(resolved),
            data=_read_json_file(resolved, field_name=field_name),
        )

    assert inline_json is not None
    return JsonInput(
        source="inline",
        path=None,
        data=_read_json_inline(inline_json, field_name=field_name),
    )


def _sha256_for_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_output_dir(output_dir: str) -> Path:
    candidate = Path(output_dir)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    resolved = candidate.resolve()
    if not _is_within(resolved, PROJECT_ROOT):
        raise ValueError(f"Output directory must stay inside repository: {resolved}")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _build_summary(
    *,
    preflight: JsonInput,
    rehearsal: JsonInput,
    human_heard: bool,
) -> Dict[str, Any]:
    preflight_ok = None
    rehearsal_ok = None
    target_status = None

    if isinstance(preflight.data, dict):
        preflight_ok = preflight.data.get("ok")
    if isinstance(rehearsal.data, dict):
        rehearsal_ok = rehearsal.data.get("ok")
        request = rehearsal.data.get("request") if isinstance(rehearsal.data.get("request"), dict) else {}
        target_status = request.get("target_status")

    return {
        "preflight_ok": preflight_ok,
        "rehearsal_ok": rehearsal_ok,
        "target_status": target_status,
        "human_heard": human_heard,
        "hardware_playback_verified": bool(human_heard),
    }


def build_acceptance_record(
    *,
    config_path: Path,
    preflight: JsonInput,
    rehearsal: JsonInput,
    human_heard: bool,
    human_note: str,
    created_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    created = created_at or datetime.now(timezone.utc)
    created = created.astimezone(timezone.utc).replace(microsecond=0)

    return {
        "schema_version": 1,
        "mode": "real_integration_acceptance_record",
        "created_at_utc": created.isoformat().replace("+00:00", "Z"),
        "notes": [
            "This record captures integration evidence only.",
            "Do not claim real hardware playback unless a human heard the output.",
        ],
        "config": {
            "path": str(config_path),
            "sha256": _sha256_for_file(config_path),
        },
        "preflight": {
            "source": preflight.source,
            "path": preflight.path,
            "data": preflight.data,
        },
        "rehearsal": {
            "source": rehearsal.source,
            "path": rehearsal.path,
            "data": rehearsal.data,
        },
        "human_confirmation": {
            "heard_audio": bool(human_heard),
            "note": human_note.strip(),
        },
        "summary": _build_summary(
            preflight=preflight,
            rehearsal=rehearsal,
            human_heard=human_heard,
        ),
    }


def _record_basename(created_at_utc: str) -> str:
    compact = created_at_utc.replace("-", "").replace(":", "").replace("T", "-").replace("Z", "Z")
    return f"acceptance-{compact}"


def _resolve_unique_basename(*, output_dir: Path, basename: str, output_format: str) -> str:
    if output_format not in {"json", "markdown", "both"}:
        raise ValueError(f"Unsupported output format: {output_format}")

    attempt = 1
    while True:
        suffix = "" if attempt == 1 else f"-{attempt}"
        candidate = f"{basename}{suffix}"
        targets: List[Path] = []
        if output_format in {"json", "both"}:
            targets.append(output_dir / f"{candidate}.json")
        if output_format in {"markdown", "both"}:
            targets.append(output_dir / f"{candidate}.md")
        if not any(path.exists() for path in targets):
            return candidate
        attempt += 1


def _to_markdown(record: Dict[str, Any]) -> str:
    config = record["config"]
    preflight = record["preflight"]
    rehearsal = record["rehearsal"]
    human = record["human_confirmation"]
    summary = record["summary"]

    lines = [
        "# Real Integration Acceptance Record",
        "",
        f"- Created (UTC): `{record['created_at_utc']}`",
        f"- Config path: `{config['path']}`",
        f"- Config sha256: `{config['sha256']}`",
        f"- Preflight source: `{preflight['source']}`",
        f"- Preflight path: `{preflight['path']}`",
        f"- Rehearsal source: `{rehearsal['source']}`",
        f"- Rehearsal path: `{rehearsal['path']}`",
        f"- Human heard audio: `{human['heard_audio']}`",
        f"- Human note: `{human['note']}`",
        "",
        "## Summary",
        "",
        f"- Preflight ok: `{summary['preflight_ok']}`",
        f"- Rehearsal ok: `{summary['rehearsal_ok']}`",
        f"- Target status: `{summary['target_status']}`",
        f"- Hardware playback verified: `{summary['hardware_playback_verified']}`",
        "",
        "## Safety Note",
        "",
        "- This record is evidence for integration behavior.",
        "- It does not prove real hardware playback unless `human_heard` is true.",
        "",
    ]
    return "\n".join(lines)


def write_acceptance_record(
    *,
    record: Dict[str, Any],
    output_dir: Path,
    output_format: str,
) -> Tuple[Optional[Path], Optional[Path]]:
    basename = _resolve_unique_basename(
        output_dir=output_dir,
        basename=_record_basename(record["created_at_utc"]),
        output_format=output_format,
    )
    json_path: Optional[Path] = None
    md_path: Optional[Path] = None

    if output_format in {"json", "both"}:
        json_path = output_dir / f"{basename}.json"
        json_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    if output_format in {"markdown", "both"}:
        md_path = output_dir / f"{basename}.md"
        md_path.write_text(_to_markdown(record), encoding="utf-8")

    return json_path, md_path


def record_acceptance_result(
    *,
    config_path: str,
    preflight_json_path: Optional[str],
    preflight_json_inline: Optional[str],
    rehearsal_json_path: Optional[str],
    rehearsal_json_inline: Optional[str],
    human_heard: bool,
    human_note: str,
    output_dir: str,
    output_format: str,
) -> Dict[str, Any]:
    config_resolved = Path(config_path).resolve()
    if not config_resolved.exists():
        raise FileNotFoundError(f"Config file not found: {config_resolved}")

    preflight = _load_optional_json_input(
        field_name="preflight",
        file_path=preflight_json_path,
        inline_json=preflight_json_inline,
    )
    rehearsal = _load_optional_json_input(
        field_name="rehearsal",
        file_path=rehearsal_json_path,
        inline_json=rehearsal_json_inline,
    )

    out_dir = _resolve_output_dir(output_dir)
    normalized_human_note = human_note.strip()
    if human_heard and not normalized_human_note:
        normalized_human_note = "Human heard playback (no additional note provided)."

    record = build_acceptance_record(
        config_path=config_resolved,
        preflight=preflight,
        rehearsal=rehearsal,
        human_heard=human_heard,
        human_note=normalized_human_note,
    )
    json_path, md_path = write_acceptance_record(
        record=record,
        output_dir=out_dir,
        output_format=output_format,
    )

    files_written = [str(path) for path in (json_path, md_path) if path is not None]
    return {
        "ok": True,
        "output_dir": str(out_dir),
        "record_json": str(json_path) if json_path else None,
        "record_markdown": str(md_path) if md_path else None,
        "files_written": files_written,
        "record": record,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Record acceptance evidence for real integration runs.")
    parser.add_argument("--config", required=True, help="Path to the config JSON used in the run")
    parser.add_argument("--preflight-json-path", help="Path to preflight JSON output")
    parser.add_argument("--preflight-json-inline", help="Inline preflight JSON object")
    parser.add_argument("--rehearsal-json-path", help="Path to rehearsal JSON output")
    parser.add_argument("--rehearsal-json-inline", help="Inline rehearsal JSON object")
    parser.add_argument("--human-heard", action="store_true", help="Set when a human actually heard playback")
    parser.add_argument("--human-note", default="", help="Optional human note for acceptance evidence")
    parser.add_argument(
        "--output-dir",
        default="acceptance_records",
        help="Output directory (relative paths are resolved under repo root)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "both"],
        default="both",
        help="Output format",
    )
    args = parser.parse_args()

    try:
        result = record_acceptance_result(
            config_path=args.config,
            preflight_json_path=args.preflight_json_path,
            preflight_json_inline=args.preflight_json_inline,
            rehearsal_json_path=args.rehearsal_json_path,
            rehearsal_json_inline=args.rehearsal_json_inline,
            human_heard=bool(args.human_heard),
            human_note=args.human_note,
            output_dir=args.output_dir,
            output_format=args.format,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
