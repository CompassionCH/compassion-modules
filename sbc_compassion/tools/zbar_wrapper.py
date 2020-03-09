##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Girardin <emmanuel.girardin@outlook.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

""" This wrapper allows to scan QRCodes thanks to the ZBar library. When no
ZBar is detected, it apply a few filter on the input image and try the
scanning again. This technique reduces the number of false negative."""
import logging

from PIL import Image

_logger = logging.getLogger(__name__)
try:
    from pyzbar import pyzbar
    import cv2  # we use openCV to repair broken QRCodes.
except ImportError:
    _logger.warning("SBC module needs pyzbar and cv2 to work.")


def scan_qrcode(filename):
    qrdata = None
    result = _decode(filename)
    # map the resulting object to a dictionary compatible with our software
    if result:
        qrdata = {}
        qrdata["data"] = result.data
        qrdata["format"] = result.type
        qrdata["raw"] = result.data
    return qrdata


def _scan(img, scanner=None):
    # convert cv image to raw data
    pil = Image.fromarray(img)
    # extract results
    qrcode = None
    for symbol in pyzbar.decode(pil):
        qrcode = symbol
    return qrcode


def _decode(filename):
    # obtain image data
    img = cv2.imread(filename, 0)

    qrcode = _scan(img)
    if not qrcode:
        # No QR found, so we try to again after an opening operation
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
        qrcode = _scan(img)

    return qrcode
