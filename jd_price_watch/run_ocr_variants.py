import pytesseract
from pathlib import Path
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
base = Path(r'C:\Users\besam\.openclaw\workspace\jd_price_watch\ocr_variants')
for p in sorted(base.glob('*.png')):
    try:
        img = Image.open(p)
        txt = pytesseract.image_to_string(img, lang='eng', config='--psm 6')
        print(f'FILE={p.name}\n{txt}\n---')
    except Exception as e:
        print(f'FILE={p.name} ERR {e}')
