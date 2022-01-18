import fitz
import glob
import time
import base64
import io
import re

from pyzbar import pyzbar
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

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


def no_ops(img):
    return img


def top_left(img):
    return img.crop([0, 0, 0.4 * img.width, 0.2 * img.height])


def greyscale(img):
    return ImageOps.grayscale(img)


def threshold(img):
    return img.point(lambda p: p > 127 and 255)


def erode(img):
    return img.filter(ImageFilter.MaxFilter(3))


def dilate(img):
    return img.filter(ImageFilter.MinFilter(3))


def contrast(img):
    return ImageEnhance.Contrast(img).enhance(2)


def rotate(i):
    def f(img):
        return img.rotate(i)
    return f


def red_channel(img):
    return img.split()[0]


def green_channel(img):
    return img.split()[1]


def blue_channel(img):
    return img.split()[2]


operations_list = [
    (top_left, blue_channel, contrast, erode,),
    (top_left, threshold,),
    (top_left,),
    (),
    (top_left, blue_channel, erode,),
    (top_left, threshold, contrast, dilate,),
    (top_left, green_channel, contrast, erode,),

    (top_left, greyscale, contrast, erode,),
    (top_left, red_channel, contrast, erode,),

    (top_left, greyscale,),
    (top_left, greyscale, erode,),
    (top_left, greyscale, dilate,),
    (top_left, greyscale, contrast, dilate,),

    (top_left, threshold, erode,),
    (top_left, threshold, dilate,),
    (top_left, threshold, contrast, erode,),
]


def find_barcode_using_multiple_strategies(original):
    for operation_list in operations_list:
        img = original.copy()
        for operation in operation_list:
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
    # Nearest is the fastest algorithm:
    # https://pillow.readthedocs.io/en/stable/handbook/concepts.html#filters-comparison-table
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


if __name__ == '__main__':
    t = time.perf_counter()
    files = glob.glob("/opt/letters/it/develStandard_With_Attachments/*.pdf")
    # files = ["SKM_C25821121012112.pdf"]
    bc = [letter_barcode_detection_pipeline(open(file, "rb").read()) for file in files]

    success = sum([a is not None for a in bc])
    total = len(bc)
    print(f"{success} / {total} = {success/total}")
    print(f"{time.perf_counter() - t} sec.")
