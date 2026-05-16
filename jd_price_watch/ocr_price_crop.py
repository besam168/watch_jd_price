import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
img = Image.open(r'C:\Users\besam\.openclaw\workspace\jd_price_watch\jd_price_crop.png')
text = pytesseract.image_to_string(img, lang='eng')
print(text)
