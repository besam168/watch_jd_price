# TradingAgents Shape A - Demo Result

## Demo script
- Script: `repo/demo_shape_a.py`
- Purpose: run a non-interactive minimal propagation using Google provider + yfinance data vendors

## Runtime inputs
- Provider: `google`
- Deep model: `gemini-2.5-flash`
- Quick model: `gemini-2.5-flash`
- Ticker: `NVDA`
- Analysis date: `2024-05-10`

## Pre-demo verification
- Unit tests passed: `logs/unit-tests.log`
  - `tests.test_model_validation`
  - `tests.test_google_api_key`

## Demo log
- `logs/demo-run.log`

## Actual outcome
The demo **really executed** and progressed into the framework runtime:
- TradingAgents graph initialized
- provider config applied
- runtime reached live LLM invocation stage
- then failed on Google model call with:
  - `404 Not Found`
  - wrapped by `ChatGoogleGenerativeAIError`

## Interpretation
This is **not** a basic installation/import failure.
It means:
- local repo import works
- local package installation works
- framework execution path works far enough to call the provider
- the current Google API/model routing in this machine environment is mismatched for `gemini-2.5-flash` via this library path

## Current demo verdict
- Install/demo chain status: **partially successful**
- Real local execution happened: **yes**
- End-to-end decision output produced: **no**
- Blocking reason: provider/model endpoint mismatch at live API call

## Next fix options
1. switch demo to a provider/model already verified on this machine for LangChain compatibility
2. inspect Google API endpoint/model naming expected by installed `langchain-google-genai` + `google-genai`
3. if desired, test OpenAI provider route separately when a compatible key is available
