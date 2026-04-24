# OpenClaw Bridge Plan Draft for TradingAgents

## Goal
Bridge the locally installed TradingAgents project into OpenClaw **without modifying existing skills**.

## Recommended bridge shape
Use a **new isolated bridge wrapper** outside the current skills tree first.

Suggested next-stage location:
- `C:\Users\besam\.openclaw\workspace\projects\tradingagents-a\bridge-draft\`

Later, if validated, promote into a separate new skill such as:
- `skills/tradingagents-bridge/`

## Why not touch current skills now
- TradingAgents is still only partially validated end-to-end on this machine
- provider compatibility is the remaining live blocker
- keeping bridge logic outside current skills avoids contaminating existing working automations

## Bridge mode recommendation
### Phase 1: local script wrapper (preferred)
OpenClaw calls a local Python wrapper script with explicit arguments.

Example inputs:
- ticker
- date
- llm_provider
- deep_model
- quick_model
- output_language
- max_debate_rounds

Example outputs:
- markdown summary
- JSON result file path
- raw log path
- success/failure status

## Wrapper contract sketch
### Command
`python run_tradingagents_bridge.py --ticker NVDA --date 2024-05-10 --provider google`

### Output
- stdout: concise final summary or error
- file artifacts:
  - `outputs/latest-result.json`
  - `outputs/latest-result.md`
  - `outputs/latest-run.log`

## OpenClaw integration options
1. **Direct exec wrapper**
   - simplest
   - low ceremony
   - best for first validation

2. **Dedicated skill later**
   - once provider routing is reliable
   - add clear parameters and usage docs
   - still keep TradingAgents repo external to skill code

3. **HTTP service later if needed**
   - only after local wrapper is stable
   - not needed for Shape A

## Proposed bridge file set for next stage
- `bridge-draft/run_tradingagents_bridge.py`
- `bridge-draft/bridge-config.example.json`
- `bridge-draft/openclaw-usage.md`

## Acceptance gate before real bridge build
Do not promote to actual OpenClaw skill until at least one live provider path returns a successful final decision from TradingAgents on this machine.
