
import os
import zbar
from PIL import Image

def decode(filename):
    # create a reader
    scanner = zbar.ImageScanner()
    # configure the reader
    scanner.parse_config('enable')

    # obtain image data
    pil = Image.open(filename).convert('L')
    width, height = pil.size
    raw = pil.tostring()

    # wrap image data
    image = zbar.Image(width, height, 'Y800', raw)

    # scan the image for barcodes
    scanner.scan(image)

    qrcode = None

    # we need a loop to extract symbol object from image.data
    for symbol in image:
        qrcode = symbol

    return qrcode
