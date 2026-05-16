from PIL import Image
from pathlib import Path

src = Path(r'C:\Users\besam\.openclaw\workspace\jd_price_watch\jd_logged_probe.png')
out = Path(r'C:\Users\besam\.openclaw\workspace\jd_price_watch\jd_price_crop.png')
img = Image.open(src)
# Based on current page layout around top-left product summary / price area
crop = img.crop((250, 430, 900, 760))
crop.save(out)
print(out)
print(crop.size)
