import os
import subprocess
import sys

SCRIPT = r"C:\Users\besam\.openclaw\workspace\skills\ppt-image-bridge\scripts\generate_image_stable.py"
OUTPUT = r"C:\Users\besam\.openclaw\workspace\skills\pptx-generator\output\child-growth-grade6.png"
PROMPT = (
    "A warm cinematic horizontal illustration for a primary school grade 6 graduation page. "
    "A Chinese child in grade 6 standing on campus at sunset, more mature and confident, holding books and looking toward the future. "
    "Include graduation mood, school building, green trees, golden light, a few classmates in the background, emotional farewell atmosphere, hopeful future feeling. "
    "Anime-realistic style, soft and touching, subtle magical natural atmosphere inspired by wholesome Japanese animated films, but no copyrighted characters. "
    "Leave some clean layout space for PPT text."
)
api_key = os.environ.get("HI_CODE_API_KEY", "")
if not api_key:
    print("Missing HI_CODE_API_KEY", file=sys.stderr)
    sys.exit(2)
cmd = [sys.executable, SCRIPT, "--prompt", PROMPT, "--provider", "openai-compatible", "--base-url", "https://api-cn.hi-code.cc/v1", "--api-key", api_key, "--model", "gpt-image-1", "--size", "1536x1024", "--output", OUTPUT, "--timeout", "300"]
result = subprocess.run(cmd, text=True)
sys.exit(result.returncode)
