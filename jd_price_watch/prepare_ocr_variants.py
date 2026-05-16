from PIL import Image, ImageOps, ImageFilter
from pathlib import Path

src = Path(r'C:\Users\besam\.openclaw\workspace\jd_price_watch\jd_logged_probe.png')
out_dir = Path(r'C:\Users\besam\.openclaw\workspace\jd_price_watch\ocr_variants')
out_dir.mkdir(parents=True, exist_ok=True)
img = Image.open(src)
# try several candidate boxes around the price area
boxes = {
    'box1': (430, 500, 900, 650),
    'box2': (450, 480, 980, 700),
    'box3': (380, 450, 980, 760),
    'box4': (500, 500, 1100, 720),
}
for name, box in boxes.items():
    crop = img.crop(box)
    crop.save(out_dir / f'{name}.png')
    gray = ImageOps.grayscale(crop)
    gray = gray.resize((gray.width*3, gray.height*3))
    gray.save(out_dir / f'{name}_gray_x3.png')
    bw = gray.point(lambda x: 0 if x < 180 else 255, '1')
    bw.save(out_dir / f'{name}_bw_x3.png')
    sharp = gray.filter(ImageFilter.SHARPEN)
    sharp.save(out_dir / f'{name}_sharp_x3.png')
print(out_dir)
