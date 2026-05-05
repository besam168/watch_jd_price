import os
import subprocess
import sys

SCRIPT = r"C:\Users\besam\.openclaw\workspace\skills\ppt-image-bridge\scripts\generate_image_stable.py"
OUTPUT = r"C:\Users\besam\.openclaw\workspace\skills\pptx-generator\output\child-growth-demo-cover.png"
PROMPT = (
    "A warm cinematic horizontal illustration for a primary school growth memory PPT cover. "
    "Show one Chinese child growing from grade 1 to grade 6 across one continuous campus scene: "
    "grade 1 small and innocent with backpack, grade 2-3 studying and playing, "
    "grade 4-5 reading confidently and joining activities, grade 6 taller and more mature looking toward the future under a tree. "
    "Anime-realistic style, gentle sunlight, lush green campus, breeze, books, paper airplanes, "
    "subtle magical forest feeling inspired by wholesome Japanese animated films, but no copyrighted characters. "
    "Soft colors, emotional, dreamy yet realistic, composition suitable for a 16:9 PowerPoint cover with clean title space on the left."
)

api_key = os.environ.get("HI_CODE_API_KEY", "")
if not api_key:
    print("Missing HI_CODE_API_KEY", file=sys.stderr)
    sys.exit(2)

cmd = [
    sys.executable,
    SCRIPT,
    "--prompt", PROMPT,
    "--provider", "openai-compatible",
    "--base-url", "https://api-cn.hi-code.cc/v1",
    "--api-key", api_key,
    "--model", "gpt-image-1",
    "--size", "1536x1024",
    "--output", OUTPUT,
    "--timeout", "300",
]

result = subprocess.run(cmd, text=True)
sys.exit(result.returncode)
