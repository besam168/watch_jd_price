# Failure Matrix

## Purpose
Provide a fast, repeatable checklist for last-hop playback validation before using a real playback target.

## Scenarios

| Scenario | Expected result | Meaning |
|---|---|---|
| 200 OK | bridge `ok=true`, player receives request | normal path works |
| 401 Unauthorized | bridge call fails, player log shows auth mismatch | token/config problem |
| 422 Entity mismatch | bridge call fails, player log shows wrong `entity_id` | target selection problem |
| 500 Forced error | bridge call fails, player log exists, target returns 500 | playback target/server problem |
| Unreachable audio URL | HTTP dispatch may succeed, but real remote player would fail to fetch media | bridge public URL problem |

## Quick commands

### 1. Normal 200 path
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\demo-http-player-roundtrip.ps1 -Text "matrix ok"
```

### 2. 401 auth failure simulation
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\demo-http-player-roundtrip.ps1 -Text "matrix auth fail" -RequireBearer secret-token
```

### 3. 422 entity mismatch simulation
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\demo-http-player-roundtrip.ps1 -Text "matrix entity fail" -RequireEntityId media_player.expected
```

### 4. 500 playback target error simulation
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\demo-http-player-roundtrip.ps1 -Text "matrix server fail" -ForcedStatus 500
```

## Interpretation rules
- If the mock player log was never created, the bridge probably never dispatched to the playback target.
- If the player log exists but bridge returned an error, inspect auth, entity_id, and returned status code.
- In the current bridge implementation, downstream 401/422/500 are surfaced back to `/speak` as upstream HTTP 500. So use the mock player record to distinguish auth failure vs entity mismatch vs target error.
- If everything is 200 locally but a real device still stays silent, focus on real target accessibility and media fetching.
