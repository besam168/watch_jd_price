---
name: responses-image-gateway
description: |
  Use when the user wants to generate an image through an OpenAI-compatible /v1/responses API endpoint with the image_generation tool, especially for smoke tests, gateway validation, or saving the returned base64 image as a local PNG. Supports normal JSON and SSE-style response.completed extraction.
---

# responses-image-gateway

Generate an image through a `/v1/responses` endpoint using shell/Python, extract the returned base64 image, and save it as a local PNG.

## When to use

Use this skill when the user wants to:
- test an OpenAI-compatible image endpoint
- call `/v1/responses` with `tools: [{"type":"image_generation"}]`
- save the generated image to a local file
- support either plain JSON responses or SSE responses containing `response.completed`

## Required inputs

Collect or define:
- `base_url` — API base URL, e.g. `https://example.com/v1/responses`
- `bearer_token`
- `prompt`

Optional:
- `model` (default: `gpt-5.4`)
- `output_path` (default: `output.png` in current working directory)

## Execution pattern

Prefer the bundled script:

```powershell
python scripts/generate_image.py \
  --url "https://example.com/v1/responses" \
  --token "YOUR_TOKEN" \
  --prompt "一只坐在咖啡杯里的柯基，日系插画风，暖色调，细节丰富，干净背景" \
  --model "gpt-5.4" \
  --output "output.png"
```

## Output behavior

On success, report only:
- whether the image was generated
- absolute path to the saved PNG

## Notes

- The script supports both regular JSON and SSE-style output.
- For SSE, it extracts `response.completed` and then finds `image_generation_call.result`.
- If the endpoint returns multiple output items, the first valid image payload is used.
