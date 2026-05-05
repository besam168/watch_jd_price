import os
import subprocess
import sys

SCRIPT = r"C:\Users\besam\.openclaw\workspace\skills\ppt-image-bridge\scripts\generate_image_stable.py"
OUTPUT = r"C:\Users\besam\.openclaw\workspace\skills\pptx-generator\output\linzeqi-totoro-cover.png"
PROMPT = (
    "A warm cinematic horizontal illustration for a primary school growth memory PPT cover with a hand-painted forest campus mood. "
    "Show a Chinese schoolgirl named Lin Zeqi growing from grade 1 to grade 6 in one continuous campus scene, with leafy trees, soft wind, sunbeams, school path, books, satchel, paper airplanes, and gentle magical countryside atmosphere. "
    "Anime-realistic, healing and nostalgic, soft green palette, watercolor-like brush texture, whimsical natural feeling, no copyrighted characters. "
    "Leave elegant title space for text on the left."
)
api_key = os.environ.get("HI_CODE_API_KEY", "")
if not api_key:
    print("Missing HI_CODE_API_KEY", file=sys.stderr)
    sys.exit(2)
cmd = [sys.executable, SCRIPT, "--prompt", PROMPT, "--provider", "openai-compatible", "--base-url", "https://api-cn.hi-code.cc/v1", "--api-key", api_key, "--model", "gpt-image-1", "--size", "1536x1024", "--output", OUTPUT, "--timeout", "300"]
result = subprocess.run(cmd, text=True)
sys.exit(result.returncode)
