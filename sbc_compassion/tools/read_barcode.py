import re

from pyzbar import pyzbar
from PIL import ImageEnhance, ImageFilter

# compile regex
reg_partner = "(?P<partner>[0-9]{7})"
reg_child = "(?P<child>[A-Z]{2}[0-9]{7,9})"
reg_optional_separator = "(?:XX)?"
reg_partner_child = re.compile(reg_partner + reg_optional_separator + reg_child, re.IGNORECASE)
reg_child_partner = re.compile(reg_child + reg_optional_separator + reg_partner, re.IGNORECASE)


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
    match = reg_partner_child.search(code) or reg_partner_child.search(code)
    if match:
        return match.group("partner"), match.group("child")
    return None, None


def letter_barcode_detection(original):
    barcode = find_barcode_using_multiple_strategies(original)
    partner, child = get_info_from_barcode(barcode)
    return partner, child
