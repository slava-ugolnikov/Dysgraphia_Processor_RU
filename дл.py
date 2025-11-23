from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"D:\Program Files\Tesseract-OCR\tesseract.exe"


img = Image.open(r"C:\Users\слава угольников\PycharmProjects\CV_Dysgraphia\грязь.png")

text = pytesseract.image_to_string(img, lang='rus')
print(text)
