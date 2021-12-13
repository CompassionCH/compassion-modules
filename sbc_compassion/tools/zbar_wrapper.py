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
    import fitz
except ImportError:
    _logger.warning("SBC module needs pyzbar, cv2 and PyMuPDF to work.")


def scan_qrcode(filename, page):
    qrdata = None
    result = _decode(filename, page)
    # map the resulting object to a dictionary compatible with our software
    if result:
        qrdata = {}
        qrdata["data"] = result.data
        qrdata["format"] = result.type
        qrdata["raw"] = result.data
    return qrdata


def _scan(img):
    # convert cv image to raw data
    pil = Image.fromarray(img)
    # extract results
    qrcode = None
    for symbol in pyzbar.decode(pil):
        qrcode = symbol
    pil.close()
    del pil
    return qrcode


def _decode(filename, page):
    # obtain image data
    img = cv2.imread(filename, 0)
    try:
        img = cv2.resize(img, None, fx=0.5, fy=0.5)
    except cv2.error:
        _logger.warning("Error resizing image for QRcode detection.")

    if img is None:
        return ""

    qr_code = _scan(img)
    del img
    if qr_code:
        return qr_code

    # No QR found, so we try to again after an opening operation

    # zoom in each dimension
    zoom = (10.0, 10.0)
    mat = fitz.Matrix(*zoom)
    pix = page.get_pixmap(matrix=mat, alpha=0)
    # store image as a PNG
    pix.save(filename)

    img_original = cv2.imread(filename, 0)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    zoom_factors = [1.0, 0.4, 0.3, 0.2, 0.6, 0.7, 0.8, 0.9]
    for zoom_factor in zoom_factors:
        try:
            img = cv2.resize(img_original, None, fx=zoom_factor, fy=zoom_factor)
            img_open = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
            del img
            qr_code = _scan(img_open)
            del img_open
            if qr_code:
                break
        except cv2.error:
            _logger.warning("Error resizing image for QRcode detection.")
    del img_original, kernel
    return qr_code
