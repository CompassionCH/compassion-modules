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
    return qrcode


def _decode(filename, page):
    # obtain image data
    img = cv2.imread(filename, 0)
    try:
        im = cv2.resize(img, None, fx=0.5, fy=0.5)
    except cv2.error:
        im = img
        _logger.warning("Error resizing image for QRcode detection.")

    if im is None:
        return ""
    qrcode = _scan(im)
    if not qrcode:
        zoom_x = 10.0  # horizontal zoom
        zomm_y = 10.0  # vertical zoom
        mat = fitz.Matrix(zoom_x, zomm_y)  # zoom factor 2 in each dimension
        # use 'mat' instead of the identity matrix
        pix = page.getPixmap(matrix=mat, alpha=0)
        pix.writePNG("page%i.png" % page.number)  # store image as a PNG
        # No QR found, so we try to again after an opening operation
        img = cv2.imread(filename, 0)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        imgage = cv2.morphologyEx(im, cv2.MORPH_OPEN, kernel)
        qrcode = _scan(imgage)
        zoom_factors = [0.4, 0.3, 0.2, 0.6, 0.7, 0.8, 0.9, 1.0]
        tries = 0
        while not qrcode and tries < len(zoom_factors):
            # No QR found, so we try to again after an opening operation
            try:
                im = cv2.resize(img, None, fx=zoom_factors[tries],
                                fy=zoom_factors[tries])
                imgage = cv2.morphologyEx(im, cv2.MORPH_OPEN, kernel)
                qrcode = _scan(imgage)
            except cv2.error:
                _logger.warning("Error resizing image for QRcode detection.")
            tries += 1
    return qrcode
