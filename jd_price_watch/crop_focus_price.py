from PIL import Image
from pathlib import Path

src = Path(r'C:\Users\besam\.openclaw\workspace\jd_price_watch\jd_logged_probe.png')
out_dir = Path(r'C:\Users\besam\.openclaw\workspace\jd_price_watch\ocr_focus')
out_dir.mkdir(parents=True, exist_ok=True)
img = Image.open(src)
# tighter boxes near expected price row under title/store block
boxes = {
    'price_row_a': (520, 560, 980, 660),
    'price_row_b': (560, 540, 1040, 680),
    'price_row_c': (600, 520, 1100, 680),
    'price_row_d': (650, 520, 1180, 700),
}
for name, box in boxes.items():
    crop = img.crop(box)
    crop.save(out_dir / f'{name}.png')
print(out_dir)
