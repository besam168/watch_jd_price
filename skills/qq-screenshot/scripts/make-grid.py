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


def row_label(idx: int) -> str:
    s = ''
    n = idx + 1
    while n > 0:
        n, rem = divmod(n - 1, 26)
        s = chr(ord('A') + rem) + s
    return s


def preset_config(preset: str):
    if preset == 'quarter':
        return {
            'cell': 40,
            'font_size': 8,
            'line_width': 1,
            'label_mode': 'rowmajor-cell',
            'margin': 2,
            'pad': 1,
        }
    if preset == 'six':
        return {
            'cell': 80,
            'font_size': 10,
            'line_width': 1,
            'label_mode': 'rowmajor-cell',
            'margin': 3,
            'pad': 2,
        }
    return {
        'cell': 40,
        'font_size': 8,
        'line_width': 1,
        'label_mode': 'rowmajor-cell',
        'margin': 2,
        'pad': 1,
    }


def add_grid(input_path: Path, output_path: Path, preset: str = 'quarter'):
    img = Image.open(input_path).convert('RGB')
    w, h = img.size
    cfg = preset_config(preset)

    cell = cfg['cell']
    cols = max(1, w // cell)
    rows = max(1, h // cell)
    step = min(w / cols, h / rows)
    grid_w = step * cols
    grid_h = step * rows
    x_offset = (w - grid_w) / 2
    y_offset = (h - grid_h) / 2

    draw = ImageDraw.Draw(img)
    line_color = (255, 0, 0)
    box_fill = (255, 255, 255)
    line_width = cfg['line_width']
    font = load_font(cfg['font_size'])
    margin = cfg['margin']
    pad = cfg['pad']

    for i in range(cols + 1):
        x = round(x_offset + i * step)
        draw.line((x, round(y_offset), x, round(y_offset + grid_h)), fill=line_color, width=line_width)
    for j in range(rows + 1):
        y = round(y_offset + j * step)
        draw.line((round(x_offset), y, round(x_offset + grid_w), y), fill=line_color, width=line_width)

    for r in range(rows):
        for c in range(cols):
            label = f"{row_label(r)}{c + 1}"
            tx = round(x_offset + c * step) + margin
            ty = round(y_offset + r * step) + margin
            bbox = draw.textbbox((tx, ty), label, font=font)
            rect = (bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad)
            draw.rectangle(rect, fill=box_fill, outline=line_color, width=1)
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
