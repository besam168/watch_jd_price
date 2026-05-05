import os
import subprocess
import sys

SCRIPT = r"C:\Users\besam\.openclaw\workspace\skills\ppt-image-bridge\scripts\generate_image_stable.py"
OUTPUT = r"C:\Users\besam\.openclaw\workspace\skills\pptx-generator\output\child-growth-grade1.png"
PROMPT = (
    "A warm cinematic horizontal illustration for a primary school grade 1 growth page. "
    "A young Chinese child entering primary school for the first time, carrying a small backpack, standing at the school gate in morning sunlight. "
    "Parents and teacher nearby in a soft supportive atmosphere, green trees, school building, gentle breeze, hopeful and innocent expression. "
    "Anime-realistic style, emotionally warm, soft colors, subtle whimsical forest feeling inspired by wholesome Japanese animation, but no copyrighted characters. "
    "Leave some clean layout space for PPT text."
)
api_key = os.environ.get("HI_CODE_API_KEY", "")
if not api_key:
    print("Missing HI_CODE_API_KEY", file=sys.stderr)
    sys.exit(2)
cmd = [sys.executable, SCRIPT, "--prompt", PROMPT, "--provider", "openai-compatible", "--base-url", "https://api-cn.hi-code.cc/v1", "--api-key", api_key, "--model", "gpt-image-1", "--size", "1536x1024", "--output", OUTPUT, "--timeout", "300"]
result = subprocess.run(cmd, text=True)
sys.exit(result.returncode)
