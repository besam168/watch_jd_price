# Real Playback Quickstart

## Goal
Use `tmall-genie-voice-bridge` with a real HTTP playback target in the shortest possible path.

## Option A: Home Assistant
1. Copy `config.home-assistant.example.json` to `config.json`.
2. Replace:
   - `HOME_ASSISTANT_HOST`
   - `BRIDGE_HOST`
   - `REPLACE_WITH_HOME_ASSISTANT_LONG_LIVED_TOKEN`
   - `media_player.tmall_genie`
3. Start bridge:
   - `powershell -NoProfile -ExecutionPolicy Bypass -File .\run-bridge.ps1 -Config .\config.json`
4. Test:
   - `powershell -NoProfile -ExecutionPolicy Bypass -File .\demo-text-roundtrip.ps1 -Text "真实播放测试" -Mode bridge -Config .\config.json`
5. Success criteria:
   - bridge returns `ok=true`
   - backend is `local_http_player`
   - Home Assistant returns HTTP 2xx
   - target device actually plays the audio

## Option B: Any HTTP playback gateway
1. Point `http_player.player_url` at the target gateway.
2. Adjust `body_template` to whatever payload that gateway expects.
3. Make sure `http_player.public_base_url` is reachable by that gateway.
4. Start bridge and run the same bridge demo.

## Fast failure checks
- If `audio_url` contains `127.0.0.1` and the player is on another machine, it will fail.
- If the player returns non-2xx, inspect auth, entity_id, and payload schema.
- If HTTP succeeds but nothing plays, the problem is now on the real playback target side, not the bridge.
