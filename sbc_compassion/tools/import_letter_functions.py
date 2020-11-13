##############################################################################
#
#    Copyright (C) 2014-2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Loic Hausammann <loic_hausammann@hotmail.com>, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
"""
Defines a few functions useful in ../models/import_letters_history.py
"""
import base64
import logging
import os
import fitz
from io import BytesIO
from time import time

from . import (
    zxing_wrapper,
    zbar_wrapper,
    patternrecognition as pr,
    checkboxreader as cbr,
)

_logger = logging.getLogger(__name__)

try:
    import numpy as np
    import cv2
    from PyPDF2 import PdfFileWriter, PdfFileReader
    from wand.image import Image as WandImage
except ImportError:
    _logger.warning("Please install numpy, cv2, PyPDF2 and wand to use SBC " "module")

##########################################################################
#                           GENERAL METHODS                              #
##########################################################################


def analyze_attachment(env, file_data, file_name, force_template):
    """
    Analyze attachment (PDF/TIFF) and save everything inside
    import_line_ids.
    The filename is given separately due to the name given by tempfile

    Beware that image is converted to 300DPI, so templates should be defined
    with 300DPI images. Scans should also be with 300 DPI for better results.

    :param env env: Odoo variable env
    :param str file_data: Binary data of the image file to analyze
    :param str file_name: Name of the image file to analyze
    :param correspondence.template force_template: Template

    :returns: Import Line values
    :rtype: list(dict)
    """
    new_dpi = 100.0
    resize_ratio = new_dpi / 300.0

    line_vals = list()
    letter_datas = list()
    _logger.info(f"\tImport file : {file_name}")

    pdf_in_buffer = BytesIO(file_data)
    inputpdf = PdfFileReader(pdf_in_buffer)
    letter_indexes, imgs, lang = _find_qrcodes(env, line_vals, inputpdf, new_dpi)
    _logger.info(f"\t {len(letter_indexes)-1 or 1} letters found!")

    # Construct the data for each detected letter: store as PDF
    if len(letter_indexes) > 1:
        last_index = 0
        for index in letter_indexes[1:]:
            inputpdf = PdfFileReader(pdf_in_buffer)
            output = PdfFileWriter()
            letter_data = BytesIO()
            for i in range(last_index, index):
                output.addPage(inputpdf.getPage(i))
            output.write(letter_data)
            letter_data.seek(0)
            letter_datas.append(letter_data.read())
            last_index = index
    else:
        letter_datas.append(file_data)

    # now try to find the layout for all splitted letters
    for i in range(len(letter_datas)):
        _logger.info(
            f"\tAnalyzing template and language of letter {i + 1}/{len(letter_datas)}"
        )

        letter_vals = line_vals[i]
        file_split = file_name.split(".")
        attach_name = file_split[0] + "-" + str(i) + ".pdf"
        letter_vals["letter_image"] = base64.b64encode(letter_datas[i])
        letter_vals["file_name"] = attach_name
        if force_template:
            letter_vals["template_id"] = force_template.id
        else:
            # use pattern recognition to find the template
            _find_template(env, imgs[i], letter_vals, resize_ratio)
            tic = time()
            if lang:
                letter_vals["letter_language_id"] = lang.id
            _logger.debug(f"\t\tLanguage analysis done in {time() - tic:.3} sec.")

    return line_vals


def _find_qrcodes(env, line_vals, inputpdf, new_dpi):
    """
    Read the image and try to find the QR codes.
    The image should be currently saved as a png with the same name
    than :py:attr:`file_` (except for the extension).
    If QR Code is in wrong orientation, this method will return the given
    file.
    In case of test, the output dictionary contains the image of the QR code
    too.

    :param env env: Odoo variable env
    :param list line_vals: Dictionary that will hold values for import line
    :param inputpdf: PDFReader of the original pdf file
    :returns: binary data of images, numpy arrays of pages to analyze further
    :rtype: list(str), list(np.array)
    """
    # Holds the indexes of the pages where a new letter is detected
    letter_indexes = list()
    page_imgs = list()

    previous_qrcode = ""
    _logger.debug(f"\tThe imported PDF is made of {inputpdf.numPages} pages.")
    # only on the first page there is a QR Code
    for i in range(1):
        tic = time()
        output = PdfFileWriter()
        output.addPage(inputpdf.getPage(i))
        page_buffer = BytesIO()
        output.write(page_buffer)
        page_buffer.seek(0)

        # read the qrcode on the current page
        qrcode, img_path = _decode_page(env, page_buffer.read())
        lang = pr.find_languages_area(env, img_path)
        if (qrcode and qrcode["data"] != previous_qrcode) or i == 0:
            previous_qrcode = qrcode and qrcode["data"]
            letter_indexes.append(i)
            # we finally resize the image before returning it
            img = cv2.imread(img_path)
            f = new_dpi / 300.0
            img = cv2.resize(img, (0, 0), fx=f, fy=f, interpolation=cv2.INTER_CUBIC)
            page_imgs.append(img)
            partner_id, child_id = decode_barcode(env, qrcode)
            page_preview = cv2.imencode(".jpg", img)
            preview_data = base64.b64encode(page_preview[1])
            values = {
                "partner_id": partner_id,
                "child_id": child_id,
                "letter_image_preview": preview_data,
            }
            _logger.debug(
                f"\t\tPage {i + 1}/{inputpdf.numPages} opened and QRCode "
                f"analyzed in {time() - tic:.2} sec"
            )
            line_vals.append(values)
        else:
            _logger.debug(
                f"\t\tPage {i + 1}/{inputpdf.numPages} opened, "
                f"no QRCode on this page. {time() - tic:.2} sec"
            )

        os.remove(img_path)
    letter_indexes.append(i + 1)

    return letter_indexes, page_imgs, lang


def _decode_page(env, page_data):
    """
    Read the image and try to find the QR codes.

    :param bytes page_data: Data of the PDF single page
    :returns: decoded qrcode, numpy array of page and test image data to show
              the detection
    :rtype: str, binary
    """
    tic = time()

    doc = fitz.open("pdf", page_data)
    for page in doc:  # iterate through the pages
        zoom_x = 5.0  # horizontal zoom
        zomm_y = 5.0  # vertical zoom

        mat = fitz.Matrix(zoom_x, zomm_y)  # zoom factor in each dimension
        pix = page.getPixmap(matrix=mat, alpha=0)  # use 'mat' instead of the identity matrix
        pix.writePNG("page%i.png" % page.number)  # store image as a PNG

    img_url = os.getcwd() + "/page0.png" # there is only one image
    decoder_lib = "zbar"
    if decoder_lib == "zxing":
        qrdata = zxing_wrapper.scan_qrcode(img_url, page)
        _logger.debug(f"\t\tQRCode decoded using ZXing in {time() - tic:.3} sec")
    elif decoder_lib == "zbar":
        qrdata = zbar_wrapper.scan_qrcode(img_url, page)
        _logger.debug(f"\t\tQRCode decoded using ZBar in {time() - tic:.3} sec")

    return qrdata, img_url


def decode_barcode(env, barcode):
    """ Split the barcode and return the id of the partner and the child.
    If the partner is not found, return None (same for the child).

    :param env: Odoo environment
    :param Barcode barcode:
    :return: partner.id, Child.id
    :rtype: int, int
    """
    partner_id = None
    child_id = None
    if barcode is not None and b"XX" in barcode["data"]:
        barcode_split = barcode["data"].split(b"XX")
        if len(barcode_split) == 2:
            partner_ref, child_code = barcode_split
            child_ref_field = "local_id"
            if len(child_code) == 9:
                # Old reference
                child_ref_field = "code"
            child_id = (
                env["compassion.child"]
                .search([(child_ref_field, "=", child_code)], order="id desc",
                        limit=1)
                .id
            )
            partner_id = (
                env["res.partner"]
                .search(
                    [("ref", "=", partner_ref), ("has_sponsorships", "=", True)],
                    limit=1,
                )
                .id
            )
    return partner_id, child_id


def _find_template(env, img, line_vals, resize_ratio):
    """
    Use pattern recognition to detect which template corresponds to img.

    :param env env: Odoo variable env
    :param img: Opencv Image to analyze
    :param dict line_vals: Dictonnary containing the data for a line
    :returns: center position of detected pattern
    :rtype: layout
    """
    templates = env["correspondence.template"].search([("pattern_image", "!=", False)])
    templates = templates.filtered(lambda t: t.pattern_image != "")
    template, result_img = pr.find_template(img, templates, resize_ratio=resize_ratio)

    if template is None:
        template = env.ref("sbc_compassion.default_template")

    line_vals["template_id"] = template.id


def _find_languages(env, img, line_vals, resize_ratio=1.0):
    """
    Crop a small part
    of the original picture around the position of each language
    check box.

    This analysis should be quite fast due to the small size of the
    pictures to analyze (should be a square of about 20-30 pixels large).

    Algorithm for finding the checked language is the following:
    1. Detect the box coordinates
    2. Compute Canny edges with two different approach and merge them
    3. Depending on the number of detected edges and a decision threshold
    we classe each box to True or False
    4. If 0 or more tha 1 box is checked, we don't return any result

    :param env env: Odoo variable env
    :param img: Image to analyze
    :param dict line_vals: Dictonnary containing the data for a line\
        (and the template)
    :returns: None
    """
    line_vals["letter_language_id"] = False
    template = env["correspondence.template"].browse(line_vals["template_id"])
    if not template:
        return

    h, w = img.shape[:2]
    checked = []
    checkbox_list = []
    for checkbox in template.checkbox_ids:
        a = int(checkbox.y_min * resize_ratio)
        b = int(checkbox.y_max * resize_ratio)
        c = int(checkbox.x_min * resize_ratio)
        d = int(checkbox.x_max * resize_ratio)
        if not (0 < a < b < h and 0 < c < d < w):
            continue
        checkbox_image = cbr.CheckboxReader(img[a: b + 1, c: d + 1])

        score = checkbox_image.compute_boxscore(boxsize=17)
        checkbox_list.append(checkbox)
        checked.append(checkbox_image.decision_threshold < score)

    checked_ind = [i for i, val in enumerate(checked) if val]
    lang = list([checkbox_list[ind] for ind in checked_ind])
    if len(lang) == 1:
        lang = lang[0].language_id
        line_vals["letter_language_id"] = lang.id


def check_file(name):
    """
    Check the name of a file.
    return 1 if it is a pdf and 0 otherwise.

    This function can be upgraded in order to include other
    format (1 for file, 2 for archive, 0 for not supported).
    In order to have a nice code, one should add the function
    is... when adding a new format

    :param str name: Name of the file to check
    :return: 1 if pdf, 2 if zip, 0 otherwise
    :rtype: int
    """
    if is_pdf(name):
        return 1
    elif is_zip(name):
        return 2
    else:
        return 0


def is_pdf(name):
    """
    Check the extension of the name

    :param string name: File name to check
    :returns: True if PDF, False otherwise
    :rtype: bool
    """
    ext = os.path.splitext(name)[1]
    return ext.lower() == ".pdf"


def is_tiff(name):
    """
    Check the extension of the name

    :param string name: File name to check
    :returns: True if TIFF, False otherwise
    :rtype: bool
    """
    ext = os.path.splitext(name)[1]
    return ext.lower() == ".tif" or ext.lower() == ".tiff"


def is_png(name):
    """
    Check the extension of the name

    :param string name: File name to check
    :returns: True if PNG, False otherwise
    :rtype: bool
    """
    ext = os.path.splitext(name)[1]
    return ext.lower() == ".png"


def is_zip(name):
    """
    Check the extension of the name

    :param string name: File name to check
    :returns: True if ZIP, False otherwise
    :rtype: bool
    """
    ext = os.path.splitext(name)[1]
    return ext.lower() == ".zip"


def find_child(env, code):
    """
    Search for a child with the code given by the partner

    :param env: Odoo's environment
    :param code: the child's code or local_id
    :return: The child, when found
    """
    field = len(code) == 9 and "code" or "local_id"
    child = env["compassion.child"].search([(field, "=", code)])
    return child


def find_partner(env, code, email):
    """
    Search for a partner given a ref or a global_id and an email
    :param env: Odoo's environment
    :param code: the partner's global_id or ref
    :param email: the partner's email
    :return: The partner, if found
    """
    partner = env["res.partner"].search(
        ["|", ("ref", "=", code), ("global_id", "=", code)]
    )
    if not partner:
        partner = env["res.partner"].search([("email", "=", email)])
    if len(partner) > 1:
        partner = partner.filtered("has_sponsorships")
    return partner[:1]
