# tmall-genie-voice-bridge

A local MVP bridge for text-to-speech and playback routing.

This project does **not** directly capture microphone audio from a real Tmall Genie device and does **not** directly push audio to Tmall Genie hardware in this repository state.

## Honest Status (2026-04-01)

Implemented:
- HTTP bridge server with `/health`, `/speak`, `/callback/text`, `/webhook/text`, `/audio/<filename>`.
- Text -> TTS file generation pipeline (`mock` and `edge` providers).
- Playback backends:
  - `mock_tmall_genie` (mock only)
  - `local_http_player` (HTTP dispatch to external player service)
  - `local_windows_speaker` (PowerShell local playback)
- Demo scripts for local text roundtrip, callback roundtrip, and WAV roundtrip.
- Lightweight smoke tests for request handling and core audio flow.

Locally tested in this environment:
- Python unit smoke tests with `unittest` (Flask test client + mock provider/backend).
- `scripts/speak.py` CLI with `config.example.json`.

Mocked / not verified here:
- Real Tmall Genie hardware playback.
- Production deployment behavior.
- Real microphone capture quality and device compatibility on every machine.

## Repository Layout

- `scripts/bridge_server.py`: Flask bridge server.
- `scripts/speak.py`: text-to-audio generation and backend dispatch.
- `scripts/listen_once.py`: one-shot speech recognition (Windows System.Speech).
- `scripts/backends/`: playback adapters.
- `scripts/providers/`: TTS providers.
- `config.example.json`: baseline config template.
- `config.local-speaker.json`: local Windows speaker demo config.
- `demo-text-roundtrip.ps1`: quick text -> speak demo.
- `demo-callback-roundtrip.ps1`: quick callback/webhook text demo.
- `demo-wav-roundtrip.ps1`: WAV transcription -> speak demo.
- `demo-http-player-roundtrip.ps1`: local HTTP player roundtrip demo.
- `run-bridge.ps1`: helper to start the bridge with a selected config.
- `run-failure-matrix.ps1`: one-shot validation runner for common last-hop success/failure scenarios.
- `scripts/mock_http_player.py`: local mock HTTP player receiver for last-hop validation.
- `scripts/rehearse-real-http-player.ps1`: preflight + one real `/speak` rehearsal runner with structured JSON summary.
- `scripts/rehearse_real_http_player.py`: underlying rehearsal implementation.
- `scripts/record-acceptance-result.ps1`: PowerShell helper to write acceptance evidence records.
- `scripts/record_acceptance_result.py`: timestamped acceptance evidence recorder (JSON/Markdown).
- `FAILURE_MATRIX.md`: quick troubleshooting matrix for HTTP playback integration.
- `HOME_ASSISTANT_ACCEPTANCE.md`: real Home Assistant bring-up and human acceptance checklist.
- `tests/test_mvp_smoke.py`: local smoke tests.
- `tests/test_acceptance_recorder.py`: targeted tests for acceptance record generation.

## Quickstart

1. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

2. Start the bridge server with mock-safe config:

```bash
python scripts/bridge_server.py --config config.example.json
```

Or:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\\run-bridge.ps1 -Config .\\config.example.json
```

3. In another terminal, call `/speak`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\demo-text-roundtrip.ps1 -Text "收到，链路可用" -Mode bridge -Config .\config.example.json
```

4. Call callback/webhook text path:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\demo-callback-roundtrip.ps1 -Text "打开客厅灯"
```

5. Local direct mode (no bridge HTTP):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\demo-text-roundtrip.ps1 -Text "本地直连测试" -Mode local -Config .\config.local-speaker.json
```

## Microphone / STT Local Testing (Windows)

The local STT path uses Windows `System.Speech` via PowerShell.
Microphone access can be healthy while recognition quality is still unstable, especially for `zh-CN`.

Preflight recognizer + microphone access:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check-microphone.ps1 -Culture zh-CN
```

Run one-shot microphone recognition with practical defaults:

```bash
python scripts/listen_once.py --culture zh-CN --timeout-seconds 8 --attempts 2
```

If microphone results are unstable, use deterministic WAV fallback in the same command:

```bash
python scripts/listen_once.py --culture zh-CN --timeout-seconds 8 --attempts 2 --fallback-wav .\tmp_audio\listen-once-test.wav
```

`listen_once.py` keeps returning JSON and now includes richer diagnostics (`installed_recognizers`, `elapsed_ms`, per-attempt results, and warnings).  
Do not treat this as proof of real hardware playback.

## Endpoint Contract

### `POST /speak`

Accepted request payload formats:
- JSON body
- `application/x-www-form-urlencoded`
- query string
- plain text body

Accepted text keys:
- `text`
- `query`
- `utterance`
- `message`
- `payload.text`
- `payload.query`
- `intent.query`
- `request.text`
- `request.query`

Minimal example:

```json
{ "text": "你好" }
```

### `POST /callback/text` and `POST /webhook/text`

Same accepted payload formats and text keys as `/speak`.

Extra callback metadata fields (optional):
- `source`
- `session_id` / `sessionId`
- `user_id` / `userId`
- `trace_id` / `traceId`
- `intent`

### `GET /audio/<filename>`

Serves generated audio files from `tts.output_dir`.

## Config Notes

- `tts.provider`: `mock` (no external TTS dependency) or `edge` (requires `edge-tts`).
- `tts.max_text_length`: optional integer guard. Default `4000`.
- `backend.type`: `mock_tmall_genie`, `local_http_player`, or `local_windows_speaker`.
- `http_player.audio_base_url`:
  - `auto`: derive from request host/proto (supports `X-Forwarded-*` headers)
  - explicit URL: fixed base for audio URLs
- `http_player.public_base_url`: if set, used as authoritative public base URL for `/audio/...` links.

## Home Assistant / Real HTTP Player Integration Notes

Recommended path for a real playback target:
- Run this bridge on a machine reachable by the playback controller.
- Set `backend.type` to `local_http_player`.
- Keep `http_player.player_url` pointed at your Home Assistant or other HTTP player endpoint.
- Do **not** leave external playback on `127.0.0.1` audio URLs unless the player runs on the same machine.

Example Home Assistant service payload pattern:

```json
{
  "entity_id": "media_player.tmall_genie",
  "media_content_id": "{{audio_url}}",
  "media_content_type": "music"
}
```

Recommended config rules:
- If Home Assistant reaches the bridge through a reverse proxy or fixed domain, set `http_player.public_base_url`.
- If the incoming request host is already the correct externally reachable address, `audio_base_url: "auto"` is acceptable.
- If the player endpoint needs auth, keep it in `http_player.headers.Authorization`.
- Start from `config.home-assistant.example.json` and replace `HOME_ASSISTANT_HOST`, `BRIDGE_HOST`, token, and `entity_id` before real testing.

Minimum real-world checklist before claiming playback is ready:
1. `/speak` returns an `audio_url` that the player machine can actually open.
2. The player endpoint returns HTTP 2xx.
3. The target device fetches the generated `/audio/...` file successfully.
4. A human confirms the device actually played the sound.

Preflight before real integration:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\preflight-real-http-player.ps1 -Config .\config.real-http-player.template.json
```

Then run a single rehearsal call against `/speak`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\rehearse-real-http-player.ps1 -Config .\config.json -BridgeUrl http://127.0.0.1:57881/speak -Text "真实联调演练"
```

What the rehearsal does:
- runs the same config preflight first
- stops before `/speak` if preflight has blocking issues (unless `-Force` is used)
- sends one real bridge request
- returns structured JSON including bridge HTTP status, `audio_url`, backend name, and surfaced target status if the playback endpoint rejects the request

Record one acceptance evidence artifact (timestamped JSON + Markdown under `acceptance_records/`):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\record-acceptance-result.ps1 `
  -Config .\config.json `
  -PreflightJsonPath .\tmp\preflight.json `
  -RehearsalJsonPath .\tmp\rehearsal.json `
  -HumanHeard `
  -HumanNote "Heard on living-room speaker at normal volume."
```

You can also pass inline JSON with `-PreflightJsonInline` / `-RehearsalJsonInline`.
This recorder is for integration evidence keeping and does not claim hardware playback unless `-HumanHeard` is set by a human.
When output filenames collide in the same second, recorder files are auto-suffixed (`-2`, `-3`, ...) instead of being overwritten.

The preflight script checks:
- whether `backend.type` is `local_http_player`
- whether auth/header placeholders are still present
- whether `Authorization` still uses the expected `Bearer ...` shape
- whether `Content-Type` still looks like JSON
- whether `entity_id` still looks like the example value
- whether `media_content_id` still contains `{{audio_url}}`
- whether Home Assistant service paths still look like `/api/services/media_player/play_media`
- whether `public_base_url` / `audio_base_url` still look local or placeholder
- whether bridge `/health` is currently reachable
- whether the playback target base URL answers a quick probe

## Validation

Run smoke tests:

```bash
python -m unittest discover -s tests -v
```

Current automated coverage includes:
- `/speak` plain text requests
- forwarded header handling for `audio_base_url: auto`
- `public_base_url` override behavior
- callback dotted-form payload parsing
- generated audio file serving from `/audio/...`
- max text length guard
- HTTP player payload rendering and dispatch

Run speak CLI directly:

```bash
python scripts/speak.py "MVP smoke check" --config config.example.json
```
