import fitz
import base64
import io
import re

from pyzbar import pyzbar
from PIL import Image, ImageEnhance, ImageFilter


def read_pdf(pdf_data):
    return fitz.Document("pdf", pdf_data)


def convert_pdf_page_to_image(page):
    mat = fitz.Matrix(4.5, 4.5)
    pix = page.get_pixmap(matrix=mat, alpha=0)
    mode = "RGBA" if pix.alpha else "RGB"
    size = [pix.width, pix.height]
    image = Image.frombytes(mode, size, pix.samples)
    return image


def detect_barcode_in_image(image):
    barcodes = pyzbar.decode(image)
    return barcodes


def top_left(img):
    return img.crop([0, 0, 0.38 * img.width, 0.15 * img.height])


def threshold(img):
    return img.point(lambda p: p > 127 and 255)


def erode(i):
    def f(img):
        return img.filter(ImageFilter.MaxFilter(i))
    return f


def contrast(i):
    def f(img):
        return ImageEnhance.Contrast(img).enhance(i)
    return f


def blue_channel(img):
    return img.split()[2]


strategies = [
    (top_left, blue_channel, contrast(2), erode(3)),
    (top_left, threshold),
    (top_left,),
    (), # do nothing
]


def find_barcode_using_multiple_strategies(original):
    for strategy in strategies:
        img = original.copy()
        for operation in strategy:
            img = operation(img)
        barcodes = detect_barcode_in_image(img)

        if len(barcodes) > 1:
            print("multiple barcode detected, used the first one")
        if barcodes:
            return barcodes[0].data.decode("utf8")

    return None


def get_info_from_barcode(code):
    if code is None:
        return None, None
    reg_partner = "([0-9]{7})"
    reg_child = "([A-Za-z]{2}[0-9]{7,9})"
    reg_optional_separator = "(?:XX)?"
    match = re.search(reg_partner + reg_optional_separator + reg_child, code)
    if match:
        return match[1], match[2]
    match = re.search(reg_child + reg_optional_separator + reg_partner, code)
    if match:
        return match[2], match[1]
    return None, None


def create_preview(image):
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    preview_b64 = base64.b64encode(buffer.getvalue())
    return preview_b64


def letter_barcode_detection_pipeline(pdf_data):
    pdf = read_pdf(pdf_data)
    page0 = next(pdf.pages())
    original = convert_pdf_page_to_image(page0)
    barcode = find_barcode_using_multiple_strategies(original)
    partner, child = get_info_from_barcode(barcode)
    preview = create_preview(original)
    return partner, child, preview
