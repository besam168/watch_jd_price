import os
import subprocess
import sys

SCRIPT = r"C:\Users\besam\.openclaw\workspace\skills\ppt-image-bridge\scripts\generate_image_stable.py"
OUTPUT = r"C:\Users\besam\.openclaw\workspace\skills\pptx-generator\output\linzeqi-totoro-grade2.png"
PROMPT = (
    "A warm whimsical horizontal illustration for a primary school grade 2 page in a cozy forest-inspired Japanese animation mood. "
    "A Chinese schoolgirl building good study habits on a green campus, reading, writing, walking with a schoolbag, with soft sunlight, leafy trees, tiny countryside details, and gentle magical atmosphere. "
    "Hand-painted anime-realistic feel, soft green and beige palette, healing and nostalgic, inspired by classic forest animation aesthetics, but do not include any copyrighted characters. "
    "Leave some clean layout space for PPT text."
)
api_key = os.environ.get("HI_CODE_API_KEY", "")
if not api_key:
    print("Missing HI_CODE_API_KEY", file=sys.stderr)
    sys.exit(2)
cmd = [sys.executable, SCRIPT, "--prompt", PROMPT, "--provider", "openai-compatible", "--base-url", "https://api-cn.hi-code.cc/v1", "--api-key", api_key, "--model", "gpt-image-1", "--size", "1536x1024", "--output", OUTPUT, "--timeout", "300"]
result = subprocess.run(cmd, text=True)
sys.exit(result.returncode)
