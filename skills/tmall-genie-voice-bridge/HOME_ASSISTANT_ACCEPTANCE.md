# Home Assistant Real Playback Acceptance

## Goal
Use this checklist when connecting `tmall-genie-voice-bridge` to a real Home Assistant playback target.

This document helps answer three questions fast:
1. Is the config filled correctly?
2. Did the bridge hand off the request correctly?
3. Did real playback actually happen?

---

## 1) Required values to replace before any real test

From `config.home-assistant.example.json`, replace all of these first:

- `HOME_ASSISTANT_HOST`
- `BRIDGE_HOST`
- `REPLACE_WITH_HOME_ASSISTANT_LONG_LIVED_TOKEN`
- `media_player.tmall_genie`

If any of the above still remain, do **not** treat the setup as ready.

---

## 2) Known-good Home Assistant shape

### `http_player.player_url`
Should normally look like:

```text
http://HOME_ASSISTANT_HOST:8123/api/services/media_player/play_media
```

### `http_player.headers.Authorization`
Should normally look like:

```text
Bearer YOUR_LONG_LIVED_TOKEN
```

### `http_player.headers.Content-Type`
Should normally be:

```text
application/json
```

### `http_player.body_template`
Should normally contain:

```json
{
  "entity_id": "media_player.YOUR_REAL_PLAYER",
  "media_content_id": "{{audio_url}}",
  "media_content_type": "music"
}
```

### `http_player.public_base_url`
Should be reachable by Home Assistant, for example:

```text
http://YOUR_BRIDGE_HOST:57881
```

If Home Assistant cannot reach this URL, the service call may succeed but playback will still fail.

---

## 3) Bring-up order

### Step A - Preflight
Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\preflight-real-http-player.ps1 -Config .\config.json
```

Expected:
- `ok: true`
- no placeholder-token issue
- no missing `entity_id`
- no missing `public_base_url` / `audio_base_url`

### Step B - Start bridge
Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run-bridge.ps1 -Config .\config.json
```

Expected:
- bridge starts cleanly
- `/health` is reachable

### Step C - Run one rehearsal
Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\rehearse-real-http-player.ps1 -Config .\config.json -BridgeUrl http://127.0.0.1:57881/speak -Text "真实播放验收"
```

Expected:
- preflight passes
- bridge request is sent
- result includes `backend=local_http_player`
- result includes `audio_url`
- if Home Assistant rejects it, result should surface `target_status`

### Step D - Human acceptance
Only call it "real playback verified" if:
- Home Assistant accepted the request
- the target device fetched the generated audio
- a human actually heard the playback

---

## 4) Failure triage

### Case 1 - Preflight fails before `/speak`
Likely causes:
- token still placeholder
- wrong backend type
- missing entity_id
- missing public audio URL config

Action:
- fix config first
- do not force past this unless debugging intentionally

### Case 2 - `/speak` fails with `target_status=401`
Likely causes:
- bad token
- missing `Bearer ` prefix
- Home Assistant token lacks access

Action:
- regenerate/check long-lived token
- confirm `Authorization: Bearer ...`

### Case 3 - `/speak` fails with `target_status=422`
Likely causes:
- wrong payload shape
- bad `entity_id`
- wrong service path

Action:
- verify `/api/services/media_player/play_media`
- verify payload keys and exact entity name

### Case 4 - `/speak` returns OK but no sound
Likely causes:
- Home Assistant accepted request but target could not fetch `audio_url`
- target device is unavailable / muted / wrong output
- player integration accepted request but did not actually play media

Action:
- open the `audio_url` from the Home Assistant side if possible
- confirm the target can reach `public_base_url`
- check Home Assistant logs / media player state

---

## 5) Honest acceptance language

### Allowed to say
- "Bridge handoff verified"
- "Home Assistant request path verified"
- "Real integration rehearsal passed"
- "Target accepted the playback request"

### Not allowed to say unless human heard it
- "Tmall Genie real playback is verified"
- "Hardware playback is complete"
- "Device definitely played audio"

---

## 6) Minimum evidence to keep

For any real acceptance run, keep these four items:
- the config file used (redact token if sharing)
- preflight JSON result
- rehearsal JSON result
- human confirmation that audio was actually heard
