import pytesseract
from pathlib import Path
from PIL import Image, ImageOps

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
img = Image.open(r'C:\Users\besam\.openclaw\workspace\jd_price_watch\jd_logged_probe.png')
# Downscale a bit then grayscale and OCR whole screenshot in sparse mode
small = img.resize((900, 1500))
gray = ImageOps.grayscale(small)
text = pytesseract.image_to_string(gray, lang='eng', config='--psm 11')
print(text)
