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
import fitz

import numpy
import zbar
import io

from kraken import binarization
from PIL import Image
from . import (
    patternrecognition as pr,
)

_logger = logging.getLogger(__name__)
try:
    from pyzbar import pyzbar
    import cv2  # we use openCV to repair broken QRCodes.
except ImportError:
    _logger.warning("SBC module needs pyzbar and cv2 to work.")


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


def _scan(img, scanner=None):
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
    im = cv2.resize(img, None, fx=0.5, fy=0.5)

    qrcode = _scan(im)
    if not qrcode:
        zoom_x = 10.0  # horizontal zoom
        zomm_y = 10.0  # vertical zoom
        mat = fitz.Matrix(zoom_x, zomm_y)  # zoom factor 2 in each dimension
        pix = page.getPixmap(matrix=mat, alpha=0)  # use 'mat' instead of the identity matrix
        pix.writePNG("page%i.png" % page.number)  # store image as a PNG
        # No QR found, so we try to again after an opening operation
        img = cv2.imread(filename, 0)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        imgage = cv2.morphologyEx(im, cv2.MORPH_OPEN, kernel)
        qrcode = _scan(imgage)
        if not qrcode:
            # No QR found, so we try to again after an opening operation
            im = cv2.resize(img, None, fx=0.4, fy=0.4)
            imgage = cv2.morphologyEx(im, cv2.MORPH_OPEN, kernel)
            qrcode = _scan(imgage)
            if not qrcode:
                # No QR found, so we try to again after an opening operation
                im = cv2.resize(img, None, fx=0.3, fy=0.3)
                imgage = cv2.morphologyEx(im, cv2.MORPH_OPEN, kernel)
                qrcode = _scan(imgage)
                if not qrcode:
                    # No QR found, so we try to again after an opening operation
                    im = cv2.resize(img, None, fx=0.2, fy=0.2)
                    imgage = cv2.morphologyEx(im, cv2.MORPH_OPEN, kernel)
                    qrcode = _scan(imgage)
                    if not qrcode:
                        # No QR found, so we try to again after an opening operation
                        im = cv2.resize(img, None, fx=0.6, fy=0.6)
                        imgage = cv2.morphologyEx(im, cv2.MORPH_OPEN, kernel)
                        qrcode = _scan(imgage)
                        if not qrcode:
                            # No QR found, so we try to again after an opening operation
                            im = cv2.resize(img, None, fx=0.7, fy=0.7)
                            imgage = cv2.morphologyEx(im, cv2.MORPH_OPEN, kernel)
                            qrcode = _scan(imgage)
                            if not qrcode:
                                # No QR found, so we try to again after an opening operation
                                im = cv2.resize(img, None, fx=0.8, fy=0.8)
                                imgage = cv2.morphologyEx(im, cv2.MORPH_OPEN, kernel)
                                qrcode = _scan(imgage)
                                if not qrcode:
                                    # No QR found, so we try to again after an opening operation
                                    im = cv2.resize(img, None, fx=0.9, fy=0.9)
                                    imgage = cv2.morphologyEx(im, cv2.MORPH_OPEN, kernel)
                                    qrcode = _scan(imgage)
                                    if not qrcode:
                                        # No QR found, so we try to again after an opening operation
                                        im = cv2.resize(img, None, fx=1.0, fy=1.0)
                                        imgage = cv2.morphologyEx(im, cv2.MORPH_OPEN, kernel)
                                        qrcode = _scan(imgage)

    return qrcode
