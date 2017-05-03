# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Girardin <emmanuel.girardin@outlook.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

""" This wrapper allows to scan QRCodes thanks to the ZBar library. When no
ZBar is detected, it apply a few filter on the input image and try the
scanning again. This technique reduces the number of false negative."""
import logging
_logger = logging.getLogger(__name__)
try:
    import zbar
    import cv2  # we use openCV to repair broken QRCodes.
    from PIL import Image
except ImportError:
    _logger.error("SBC module needs zbar, cv2 and PIL to work.")


def scan_qrcode(filename):
    qrdata = None
    result = _decode(filename)
    # map the resulting object to a dictionary compatible with our software
    if result:
        qrdata = {}
        qrdata["data"] = result.data
        qrdata["format"] = result.type
        qrdata["points"] = result.location
        qrdata["raw"] = result.data
    return qrdata


def _scan(img, scanner=None):
    # convert cv image to raw data
    pil = Image.fromarray(img)
    width, height = pil.size
    raw = pil.tobytes()
    # wrap image data
    image = zbar.Image(width, height, 'Y800', raw)

    if not scanner:
        # create a reader
        scanner = zbar.ImageScanner()
        # configure the reader
        scanner.parse_config('enable')

    # scan the image for barcodes
    scanner.scan(image)
    # extract results
    qrcode = None
    for symbol in image:
        qrcode = symbol
    return qrcode


def _decode(filename):
    # create a reader
    scanner = zbar.ImageScanner()
    # configure the reader
    scanner.parse_config('enable')

    # obtain image data
    img = cv2.imread(filename)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    qrcode = _scan(img, scanner=scanner)
    if not qrcode:
        # No QR found, so we try to again after an opening operation
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
        qrcode = _scan(img, scanner=scanner)

    return qrcode
