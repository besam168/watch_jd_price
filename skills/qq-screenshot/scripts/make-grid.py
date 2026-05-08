from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def load_font(size: int):
    candidates = [
        'arial.ttf',
        'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/msyh.ttc',
        'C:/Windows/Fonts/segoeui.ttf',
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            continue
    return ImageFont.load_default()


def add_grid(input_path: Path, output_path: Path, preset: str = 'quarter'):
    img = Image.open(input_path).convert('RGB')
    w, h = img.size

    if preset == 'quarter':
        cols = 4
        rows = 4
    elif preset == 'six':
        cols = 6
        rows = 6
    else:
        cols = 4
        rows = 4

    step_x = w / cols
    step_y = h / rows

    draw = ImageDraw.Draw(img)
    line_color = (255, 0, 0)
    box_fill = (255, 255, 255)
    line_width = max(2, int(min(w, h) / 500))
    font = load_font(max(18, int(min(w, h) / 35)))

    for i in range(1, cols):
        x = round(i * step_x)
        draw.line((x, 0, x, h), fill=line_color, width=line_width)
    for j in range(1, rows):
        y = round(j * step_y)
        draw.line((0, y, w, y), fill=line_color, width=line_width)

    for c in range(cols):
        for r in range(rows):
            label = f"{chr(ord('A') + c)}{r + 1}"
            x0 = round(c * step_x)
            y0 = round(r * step_y)
            tx = x0 + 10
            ty = y0 + 10
            bbox = draw.textbbox((tx, ty), label, font=font)
            pad = 6
            rect = (bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad)
            draw.rounded_rectangle(rect, radius=6, fill=box_fill, outline=line_color, width=2)
            draw.text((tx, ty), label, fill=line_color, font=font)

    img.save(output_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--preset', default='quarter')
    args = parser.parse_args()
    add_grid(Path(args.input), Path(args.output), args.preset)
    print(str(Path(args.output)))
