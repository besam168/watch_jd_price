# tmall-genie-voice-bridge

A local MVP bridge for text-to-speech, speech capture, wake-word prototyping, and playback routing.

This project does **not** directly capture microphone audio from a real Tmall Genie device and does **not** directly push audio to Tmall Genie hardware in this repository state.

## Honest Status (2026-04-06)

Implemented:
- HTTP bridge server with `/health`, `/speak`, `/callback/text`, `/webhook/text`, `/audio/<filename>`.
- Text -> TTS file generation pipeline (`mock` and `edge` providers).
- Playback backends:
  - `mock_tmall_genie` (mock only)
  - `local_http_player` (HTTP dispatch to external player service)
  - `local_windows_speaker` (PowerShell local playback)
- One-shot microphone / WAV speech input via `scripts/listen_once.py`.
- Wake-word prototype loop via `scripts/wake_loop.py`.
- Preflight + rehearsal + acceptance-record tooling for real HTTP playback bring-up.
- Lightweight smoke tests for request handling and core audio flow.

Locally tested in this environment:
- Python unit smoke tests with `unittest`.
- `scripts/speak.py` CLI with `config.example.json`.
- Local Windows speaker path now prefers **silent/background playback via MCI (`winmm.dll`)** for MP3.
- WAV local playback continues to use `SoundPlayer`.
- `WMPlayer COM` is retained as a secondary fallback path.
- Shell-open fallback exists for recovery only and may open a visible player window.
- **Human-heard validation passed for local silent/background playback on this machine.**
- Microphone capture works with the Logitech C270 webcam microphone.
- Local Whisper works on captured WAV files and has successfully recognized Chinese short phrases in live tests.
- Wake-word MVP has triggered at least once in local testing and replied with local TTS, but stability still needs improvement.

Mocked / not verified here:
- Real Tmall Genie hardware playback.
- Production deployment behavior.
- Real microphone capture quality and device compatibility on every machine.
- Home Assistant -> target device -> audible playback proof in a real home environment.
- Product-grade wake-word stability.

## Claim Boundary

You may honestly claim:
- "Local bridge flow works."
- "HTTP handoff to a playback target is implemented."
- "Preflight and rehearsal tooling exist for real-player bring-up."
- "Integration evidence can be recorded with a timestamped artifact."
- "Local silent/background playback is currently available on this Windows machine."
- "Local silent/background playback has passed human-heard validation on this machine."
- "Microphone capture + local Whisper transcription has been wired up and works in local experiments."
- "Wake-word MVP exists and has triggered successfully in at least one local test."

You may **not** honestly claim unless a human confirmed it:
- "Real Tmall Genie playback is verified."
- "Hardware playback is complete."
- "The device definitely played audio."
- "The microphone / callback / wake-word path is production-ready on real hardware."
- "Wake-word detection is already stable enough for always-on unattended use."

## Repository Layout

- `scripts/bridge_server.py`: Flask bridge server.
- `scripts/speak.py`: text-to-audio generation and backend dispatch.
- `scripts/listen_once.py`: one-shot speech recognition (Windows System.Speech or local Whisper path).
- `scripts/wake_loop.py`: wake-word prototype loop for fast local wake-response testing.
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
powershell -NoProfile -ExecutionPolicy Bypass -File .\run-bridge.ps1 -Config .\config.example.json
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

## Local Windows Speaker Notes

Current preferred local playback path:
- `local_windows_speaker.py` should invoke the configured `local_windows_speaker.player_script`
- `play-local-audio.ps1` should prefer **MCI (`winmm.dll`)** for MP3 silent/background playback
- WAV local playback should continue to use `SoundPlayer`
- `WMPlayer COM` is a secondary fallback path
- shell-open fallback is recovery-only and may open a visible player window

Important nuance:
- `WMPlayer` state alone is not the same as human-heard confirmation
- final local acceptance should always include a human-heard check

## Microphone / STT Local Testing (Windows)

The local STT path uses either:
- Windows `System.Speech` (best-effort, weaker for Chinese), or
- Local Whisper (preferred on this machine)

Recommended local Chinese testing path:

```bash
python scripts/listen_once.py --engine local_whisper --culture zh-CN --keep-recorded-wav
```

Current stable defaults in `listen_once.py` are tuned for local experiments on this machine:
- fixed default mic device: `麦克风 (Logi C270 HD WebCam)`
- longer capture window for normal dictation
- pre-roll delay before capture
- raw audio level summary
- cleaned audio level summary
- preprocessing before Whisper

### Preprocessing modes

`listen_once.py` now supports two preprocessing modes:
- `standard`:
  - for normal dictation / one-shot transcription
  - uses highpass + lowpass + silence removal + loudness normalization
- `wake`:
  - for short wake phrases
  - uses lighter preprocessing to avoid over-trimming short utterances

Examples:

```bash
python scripts/listen_once.py --engine local_whisper --culture zh-CN --preprocess-mode standard
```

```bash
python scripts/listen_once.py --engine local_whisper --culture zh-CN --preprocess-mode wake --timeout-seconds 3 --pre-roll-seconds 0.2
```

### What to look at in the JSON output

For debugging, pay attention to:
- `level_summary`
- `cleaned_level_summary`
- `likely_silent`
- `likely_too_quiet_for_stt`
- `recorded_wav_path`
- `cleaned_wav_path`
- `preprocess_filter_chain`

Interpretation:
- audio may be present but still too weak for reliable STT
- short Chinese replies like `在` are much harder than longer replies like `我在`
- wake-word detection should not reuse the exact same preprocessing strategy as normal dictation

## Wake-Word MVP

`scripts/wake_loop.py` is currently a **wake-word MVP**, not a product-grade always-on detector.

### Current goal
- Say a wake phrase such as `啊三在吗`
- System responds locally with `我在`

### Current characteristics
- Uses `local_whisper`
- Uses fast capture defaults for responsiveness
- Uses `preprocess_mode="wake"`
- Uses local silent/background playback for the reply
- Supports fuzzy wake variants like `啊三`, `阿三`, `阿山`, `啊山`, and `啊三在吗`

### Important limitation
Wake-word triggering has worked in local testing at least once, but it is **not yet stable enough** for unattended always-on use.
Current remaining work is mainly around:
- reducing latency
- improving short-phrase stability
- balancing wake responsiveness vs false negatives

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

### `GET /audio/<filename>`

Serves generated audio files from `tts.output_dir`.

## Home Assistant / Real HTTP Player Integration Notes

Recommended path for a real playback target:
- Run this bridge on a machine reachable by the playback controller.
- Set `backend.type` to `local_http_player`.
- Keep `http_player.player_url` pointed at your Home Assistant or other HTTP player endpoint.
- Do **not** leave external playback on `127.0.0.1` audio URLs unless the player runs on the same machine.

Minimum real-world checklist before claiming playback is ready:
1. `/speak` returns an `audio_url` that the player machine can actually open.
2. The player endpoint returns HTTP 2xx.
3. The target device fetches the generated `/audio/...` file successfully.
4. A human confirms the device actually played the sound.

## Validation

Run smoke tests:

```bash
python -m unittest discover -s tests -v
```

Run speak CLI directly:

```bash
python scripts/speak.py "MVP smoke check" --config config.example.json
```
