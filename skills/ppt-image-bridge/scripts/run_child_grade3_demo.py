import os
import subprocess
import sys

SCRIPT = r"C:\Users\besam\.openclaw\workspace\skills\ppt-image-bridge\scripts\generate_image_stable.py"
OUTPUT = r"C:\Users\besam\.openclaw\workspace\skills\pptx-generator\output\child-growth-grade3.png"
PROMPT = (
    "A warm cinematic horizontal illustration for a primary school grade 3 growth page. "
    "A Chinese child in grade 3 discovering interests and confidence, reading a book under a tree on campus and sharing ideas with classmates. "
    "Show curiosity, creativity, paper airplanes, books, sunshine through leaves, playful but focused mood. "
    "Anime-realistic style, gentle and emotional, soft colors, slightly magical natural atmosphere inspired by wholesome Japanese animated films, but no copyrighted characters. "
    "Leave some clean layout space for PPT text."
)
api_key = os.environ.get("HI_CODE_API_KEY", "")
if not api_key:
    print("Missing HI_CODE_API_KEY", file=sys.stderr)
    sys.exit(2)
cmd = [sys.executable, SCRIPT, "--prompt", PROMPT, "--provider", "openai-compatible", "--base-url", "https://api-cn.hi-code.cc/v1", "--api-key", api_key, "--model", "gpt-image-1", "--size", "1536x1024", "--output", OUTPUT, "--timeout", "300"]
result = subprocess.run(cmd, text=True)
sys.exit(result.returncode)
