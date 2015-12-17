# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Loic Hausammann <loic_hausammann@hotmail.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
"""
Defines a few functions useful in ../models/import_mail.py
"""
import csv
import os
import cv2
import base64
import zxing
import tempfile
import patternrecognition as pr
import checkboxreader as cbr
import bluecornerfinder as bcf
import numpy as np
from math import ceil
from glob import glob
from wand.image import Image
from collections import namedtuple

from openerp import _, exceptions

##########################################################################
#                           GENERAL METHODS                              #
##########################################################################


def testline(env, line_vals, csv_file_ids, doc_name):
    """ Test each line and verify the data given by the csv.
    A csv file need to be written in the same way than
    sbc_compassion/tests/testdata/import/travis_file.csv

    :param env: Odoo environment
    :param dict line_vals: Dictionnary that will be used to create line
    :param Recordset('ir.attachment') csv_file_ids: CSV used to check
    :param str doc_name: Document name
    :returns: Error detected
    :rtype: str
    """
    # str that will be returned
    error = ''
    csv_data = []
    # creates a list containing all the csv data
    for csv_ in csv_file_ids:
        if os.path.splitext(csv_.name)[1] != '.csv':
            raise exceptions.Warning(
                _("File '{}' is not a csv file".format(csv_.name)))
        csv_string = base64.b64decode(csv_.datas).splitlines()
        csv_data += read_csv(csv_string)
    # check that the letter is present in the csv file and find it
    values = {}
    for csv_line in csv_data:
        if csv_line['name'] == doc_name:
            values = csv_line
            break
    else:
        raise exceptions.Warning(
            _("File '{}' not found in the csv files".format(doc_name)))
    # Test that the template is the same as given in the csv
    template_csv = env.ref(
        'sbc_compassion.'+values['template_id'])
    if template_csv.id != line_vals['template_id']:
        error = error + 'template,\n'

    # Test that the barcode detection matches the result given in csv file
    BarcodeTuple = namedtuple('BarcodeTuple', ['data'])
    barcode = BarcodeTuple(values['barcode'])
    partner_detected, child_detected = decodeBarcode(env, barcode)
    # 1) we check the case where the barcode was not detected and was not
    # expected
    if (line_vals['child_id'] != child_detected or
            line_vals['partner_id'] != partner_detected):
        error = error + 'barcode,\n'

    # Test that languages detected are the same as given in the csv file
    lang_ok = True
    letter_languages_id = line_vals['test_letter_languages_id'].split(',')
    for lang in letter_languages_id:
        lang_ok = lang_ok and lang in values['lang']
    line_nber_lang = len(letter_languages_id)
    csv_nber_lang = len(values['lang'].split(','))
    lang_ok = lang_ok and line_nber_lang == csv_nber_lang

    if not lang_ok:
        error = error + 'lang,\n'

    # remove the two last character (',\n')
    return error[:-2]


def update_stat_text(test_import):
    """ Update the text for the stats in test_import ("12/34 (35.3%)").
    Test is used in order to know if the number of passed test needs to be
    increased.
    :param test.import.letters.history test_import: Item to check
    :returns: Updated Item
    :rtype: test.import.letters.history
    """
    test = 0
    qr = 0
    tpl = 0
    lang = 0
    for line in test_import.test_import_line_ids:
        if len(line.error) > 0:
            test += 1
        if 'template' in line.error:
            tpl += 1
        if 'barcode' in line.error:
            qr += 1
        if 'lang' in line.error:
            lang += 1

    test = test_import.nber_test - test
    tpl = test_import.nber_test - tpl
    qr = test_import.nber_test - qr
    lang = test_import.nber_test - lang

    test_import.test_ok = write_text_test(test, test_import.nber_test)
    test_import.qr_ok = write_text_test(qr, test_import.nber_test)
    test_import.lang_ok = write_text_test(lang, test_import.nber_test)
    test_import.template_ok = write_text_test(tpl, test_import.nber_test)
    return test_import


def write_text_test(nber, tot):
    ratio = float(nber) / float(tot)
    text = str(nber) + '/' + str(tot) + ' (' + str.format(
        "{0:.2f}", 100*ratio) + '%)'
    return text


def analyze_attachment(env, file_, filename, force_template, test=False):
    """
    Analyze attachment (PDF/TIFF) and save everything inside
    import_line_ids.
    The filename is given separately due to the name given by tempfile
    The test parameter is used to know if a real line needs to be created
    or a test.import.letter.line.

    :param env env: Odoo variable env
    :param str file_: Path of the file to analyze
    :param str filename: Filename to give in odoo
    :param sponsorship.correspondence.template force_template: Template
    :param bool test: Test import or not

    :returns: Import Line values, IR Attachment values
    :rtype: dict, dict
    """
    line_vals = {}
    document_vals = {}

    # convert to PNG
    if isPDF(file_) or isTIFF(file_):
        name = os.path.splitext(file_)[0]
        with Image(filename=file_) as img:
            img.format = 'png'
            img.save(filename=name + '.png')
        file_png = name + '.png'
    # now do the computations only if the image is a PNG
    img = cv2.imread(file_png)
    is_multipage = False
    if img is None:
        file_png = name + '-0' + '.png'
        img = cv2.imread(file_png)
        is_multipage = True
        if img is None:
            raise exceptions.Warning(
                "The '{}' image cannot be read".format(filename))
    # first compute the QR code
    data, img = _find_qrcode(env, line_vals, img, is_multipage, file_, test)
    document_vals = {
        'name': filename,
        'datas': base64.b64encode(data),
        'datas_fname': filename,
    }

    # now try to find the layout
    # loop over all the patterns in the pattern directory
    pattern_center = _find_template(env, img, line_vals, test)
    if line_vals['template_id'] != env.ref(
            'sbc_compassion.default_template').id:
        _find_languages(env, img, pattern_center, line_vals, test)
    else:
        line_vals['letter_language_id'] = False
        if test:
            line_vals.update({
                'lang_preview': '',
                'test_letter_languages_id': ''
            })
    if force_template:
        line_vals['template_id'] = force_template.id

    # Downsize png image for saving it in a preview field
    with Image(filename=file_png) as img:
        img.resize(img.width/4, img.height/4)
        line_vals['letter_image_preview'] = base64.b64encode(img.make_blob())

    # Remove all temp files written to disk
    os.remove(file_png)
    if is_multipage:
        delfiles = glob(name + '*png')
        for file_ in delfiles:
            os.remove(file_)

    return line_vals, document_vals


def _find_qrcode(env, line_vals, img, is_multipage, file_, test):
    """
    Read the image and try to find the QR code.
    The image should be currently saved as a png with the same name
    than file_ (except for the extension).
    If QR Code is in wrong orientation, this method will return the given
    file.
    In case of test, the output dictonnary contains the image of the QR code
    too.

    :param env env: Odoo variable env
    :param dict line_vals: Dictionary that will hold values for import line
    :param np.array img: Image to analyze
    :param bool is_multipage: If the file is multipage
    :param file_: Name of the temporary file
    :param bool test: Save the image of the QR code or not
    :returns: data, img
    :rtype: str, np.array
    """
    name = os.path.splitext(file_)[0]
    file_png = name + '.png'
    f = open(file_)
    data = f.read()
    f.close()
    if is_multipage:
        file_png = name + '-0' + '.png'
    # get size and position
    img_height, img_width = img.shape[:2]
    left = img_width * float(
        env['ir.config_parameter'].get_param(
            'qrcode_x_min'))
    top = img_height * float(
        env['ir.config_parameter'].get_param(
            'qrcode_y_min'))
    width = img_width * float(
        env['ir.config_parameter'].get_param(
            'qrcode_x_max'))
    width -= left
    height = img_height * float(
        env['ir.config_parameter'].get_param(
            'qrcode_y_max'))
    height -= top
    # decoder
    zx = zxing.BarCodeTool()
    # first attempt
    qrcode = zx.decode(file_png, try_harder=True, crop=[
        int(left), int(top), int(width), int(height)])
    if test:
        right = int(left)+int(width)
        bottom = int(top) + int(height)
        test_img = cv2.imread(file_png)[int(top):bottom, int(left):right]
        test_data = readEncode(test_img)
    # check if found, if not means that page is rotated
    if qrcode is None:
        # rotate image
        img = img[::-1, ::-1]
        # second attempt
        cv2.imwrite(file_png, img)
        qrcode = zx.decode(file_png, try_harder=True, crop=[
            int(left), int(top), int(width), int(height)])
        # if the QR code is found
        if qrcode is not None and testDirectionQRcode(qrcode):
            right = int(left)+int(width)
            bottom = int(top) + int(height)
            test_img = cv2.imread(file_png)[int(top):bottom, int(left):right]
            test_data = readEncode(test_img)
            # save it for zxing
            cv2.imwrite(file_png, img)
            # replace the image by the returned one
            data = _save_img(is_multipage, file_, img)
        else:
            img = img[::-1, ::-1]
            cv2.imwrite(file_png, img)
            qrcode = zx.decode(file_png, try_harder=True)

    partner_id, child_id = decodeBarcode(env, qrcode)

    line_vals.update({
        'partner_id': partner_id,
        'child_id': child_id,
    })
    if test:
        line_vals.update({
            'qr_preview': test_data
        })
    return data, img


def testDirectionQRcode(barcode):
    """ Test if the direction of the QR code is correct
    :param Barcode barcode: Data from zxing
    :return: True if the qrcode is in the right direction
    :rtype: bool
    """
    # vector between the two uppermost points (index 1 is
    # the one at the upper leftmost corner)
    top = np.array(barcode.points[2]) - np.array(barcode.points[1])
    left = np.array(barcode.points[0]) - np.array(barcode.points[1])
    diag = top + left
    if diag[0] > 0 < diag[1]:
        return True
    else:
        return False


def decodeBarcode(env, barcode):
    """ Split the barcode and return the id of the partner and the child.
    If the partner is not found, return None (same for the child).
    :param env: Odoo environment
    :param Barcode barcode:
    :return: partner.id, Child.id
    :rtype: int, int
    """
    partner_id = None
    child_id = None
    if barcode is not None and 'XX' in barcode.data:
        barcode_split = barcode.data.split('XX')
        if len(barcode_split) == 2:
            partner_ref, child_code = barcode_split
            child_id = env['compassion.child'].search(
                [('code', '=', child_code)]).id
            partner_id = env['res.partner'].search(
                [('ref', '=', partner_ref),
                 ('is_company', '=', False)]).id
    return partner_id, child_id


def readEncode(img, format_img='png'):
    """
    Create a tempfile, write the image on it and return a base64 encoded
    string
    :param np.array img: Image
    :param str format_img: Format image
    :returns: Data (encoded in base64)
    :rtype: str
    """
    with tempfile.NamedTemporaryFile(suffix='.'+format_img) as temp_file:
            cv2.imwrite(temp_file.name, img)
            f = open(temp_file.name)
            test_data = f.read()
            f.close()
    return base64.b64encode(test_data)


def _save_img(is_multipage, file_, img):
    """
    This method is called when an image is scanned in the wrong direction.
    It consists in saving the image (returning is already done before).
    In case of multipage, the pages need to be returned.

    :param bool is_multipage: If the file is a multipage one
    :param str file_: Name of the file
    :param np.array img: Image
    :returns: Data contained in the file
    :rtype: str
    """
    # if multipage, needs to turn all of them
    name = os.path.splitext(file_)[0]
    if is_multipage:
        file_png = name + '-0' + '.png'
        # Get list of all image file names to include
        image_names = glob(name + '-*.png')
        for g in image_names:
            # first page already done
            if file_png != g:
                img_temp = cv2.imread(g)[::-1, ::-1]
                cv2.imwrite(g, img_temp)

        # Create new Image, and extend sequence
        # put first page at the beginning
        with Image() as img_tiff:
            img_tiff.sequence.extend(
                [Image(filename=img_name)
                 for img_name in sorted(image_names)])
            img_tiff.save(filename=file_)
            f = open(file_)
            data = f.read()
            f.close()
    # case with only one page
    else:
        file_png = name + '.png'
        cv2.imwrite(file_, img)
        f = open(file_)
        data = f.read()
        f.close()
    return data


def _find_template(env, img, line_vals, test):
    """
    Use pattern recognition to detect which template corresponds to img.
    :param env env: Odoo variable env
    :param img: Image to analyze
    :param dict line_vals: Dictonnary containing the data for a line
    :param bool test: Enable the test mode (will save some img)
    :returns: center position of detected pattern
    :rtype: layout
    """
    templates = env['sponsorship.correspondence.template'].search(
        [('pattern_image', '!=', False)])
    threshold = float(
        env.ref('sbc_compassion.threshold_keypoints_template').value)
    template, pattern_center, img = pr.find_template(
        img, templates, threshold=threshold, test=test)
    if test:
        img = manyImages2OneImage(img, 1)
        line_vals['template_preview'] = img

    if template is None:
        pattern_center = np.array(([0, 0], [0, 0]))
        template = env.ref('sbc_compassion.default_template')

    line_vals['template_id'] = template.id
    return pattern_center


def _find_languages(env, img, pattern_center, line_vals, test):
    """
    Use the pattern and the blue corner for doing a transformation
    (rotation + scaling + translation) in order to crop a small part
    of the original picture around the position of each language
    check box.
    The rotation matrix is given by R, the scaling one by scaling
    and the translaion by C.
    The rotation angle :math:`\theta` is given by the angle between
    the template and image vectors that start from the blue square (B)
    and end at the pattern.
    The scaling is given in a matrix form where math:`S_1` is the
    ratio between the width of the image and the one of the template
    (same for the height with :math:`S_2`)
    The translation vector is constructed from the two previous matrices
    and the two vectors B (in the image) and B' (in the template)
    .. math::
      R = \left(\begin{array}{cc}
        \cos(\theta) & -\sin(\theta) \\
        \sin(\theta) & \cos(\theta)  \end{array}
      \right)

      \text{scaling} = \left(\begin{array}{cc}
        S_1 & 0 \\
        0 & S_2  \end{array}
      \right)

      C = B-R*B'
    This analysis should be quite fast due to the small size of the
    pictures to analyze (should be a square of about 20-30 pixels large).

    :param env env: Odoo variable env
    :param img: Image to analyze
    :param pattern_center: Center position of detected pattern
    :param dict line_vals: Dictonnary containing the data for a line
    (and the template)
    :param bool test: Enable the test mode (will save some img)
    :returns: None
    """
    line_vals['letter_language_id'] = False
    if test:
        # The color order is BGR
        lang_color = (0, 97, 232)
        corner_color = (0, 255, 0)

        line_vals.update({
            'lang_preview': '',
            'test_letter_languages_id': ''
        })

    # if pattern has not been detected
    if pattern_center is None:
        return

    template = env['sponsorship.correspondence.template'].browse(
        line_vals['template_id'])
    # get position of the blue corner
    box = [float(
        env['ir.config_parameter'].get_param('bluecorner_x_min')),
        float(
        env['ir.config_parameter'].get_param('bluecorner_y_max'))]
    bluecorner = bcf.BlueCornerFinder(img, box=box)
    bluecorner_position = bluecorner.getIndices()
    if bluecorner_position is None:
        return

    # vector between the blue square and the pattern
    diff_ref = np.array(template.get_bluesquare_area() -
                        template.get_pattern_center())
    diff_scan = np.array(bluecorner_position-pattern_center)
    # need normalized vectors
    normalization = (np.linalg.norm(diff_ref) *
                     np.linalg.norm(diff_scan))
    # angle between the scan and the ref image
    costheta = np.dot(diff_ref, diff_scan)/normalization
    sintheta = np.linalg.det([diff_ref, diff_scan])/normalization

    # rotation matrix
    R = np.array([[costheta, -sintheta], [sintheta, costheta]])

    # scaling matrix (use image size)
    scaling = np.array(bluecorner.getSizeOriginal(), dtype=float) / \
        np.array(template.get_template_size(), dtype=float)
    scaling = np.array([[scaling[0], 0], [0, scaling[1]]])

    # transformation matrix
    R *= scaling
    # translation vector
    C = bluecorner_position-np.dot(R, template.get_bluesquare_area())
    h, w = img.shape[:2]

    # now for the language

    # language
    lang = []
    if test:
        test_img = []
    # first loop to write the image and find the language
    for checkbox in template.checkbox_ids:
        a = checkbox.y_min
        b = checkbox.y_max
        c = checkbox.x_min
        d = checkbox.x_max
        # transform the coordinate system
        (a, b) = np.round(np.dot(R, np.array([a, b])) + C)
        (c, d) = np.round(np.dot(R, np.array([c, d])) + C)
        # new name (if changed, need to change in the remove loop)
        if not (0 < a < b < h and 0 < c < d < w):
            continue
        A = cbr.CheckboxReader(img[a:b+1, c:d+1])
        if test:
            pos = (int(checkbox.x_max-checkbox.x_min)/2,
                   int(checkbox.y_max-checkbox.y_min)/2)
            img_lang = np.copy(img[a:b+1, c:d+1])
            code_iso = checkbox.language_id.code_iso
            if code_iso:
                cv2.putText(img_lang, code_iso, pos,
                            cv2.FONT_HERSHEY_SIMPLEX, 1,
                            lang_color)
            for corners in A.corners:
                img_lang[corners] = corner_color
            test_img.append(img_lang)
        # if something happens
        # if A.test is True or A.getState is True or A.getState is None:
        if A.getState() is True:
            lang.append(checkbox.language_id.id)
    if test:
        test_data = manyImages2OneImage(test_img, 2)
        test_lang = ''
        for l in lang:
            lang_db = env['res.lang.compassion'].search([
                ('id', '=', l)])
            if lang_db:
                test_lang = test_lang + lang_db.code_iso + ','
            else:
                test_lang = test_lang + 'other,'

        line_vals.update({
            'lang_preview': test_data,
            'test_letter_languages_id': test_lang[:-1]
        })
    if len(lang) == 1:
        lang = lang[0]
        line_vals['letter_language_id'] = lang
    return line_vals


def manyImages2OneImage(test_img, col):
    """ Create an image from a list of image
    by creating a layout (with col columns)
    :param list test_img: list of array
    :param int col: Number of columns wanted
    """
    row = int(ceil(float(len(test_img)) / col))
    # first compute size of the final image
    height_img = 0
    width_img = 0
    for r in range(row):
        stop = min((r+1)*col, len(test_img))
        height_row, width_row = computeRowSize(test_img[r*col:stop])
        height_img += height_row
        if width_row > width_img:
            width_img = width_row
    # image that will be returned (initially black)
    # + col+1 is done for having at least 1 pixel between each
    # column (same for row)
    height_img += row + 1
    width_img += col + 1
    img = np.zeros((height_img, width_img, 3), np.uint8)
    top = 1
    for r in range(row):
        stop = min((r+1)*col, len(test_img))
        height_row, width_row = computeRowSize(test_img[r*col:stop])
        left = 1
        col_temp = col
        # last index computation a little bit different
        if r != row - 1:
            pad_left = (width_img - width_row) / (col_temp + 1)
        else:
            col_temp = len(test_img) - col*row
            if col_temp == 0:
                col_temp = col
            pad_left = (width_img - width_row) / (col_temp + 1)
        for c in range(col_temp):
            h, w = test_img[r*col+c].shape[:2]
            left += pad_left
            pad_top = (height_row - h) / 2
            top_cell = top + pad_top
            img[top_cell:top_cell+h, left:left+w] = test_img[r*col+c]
            left += w
        top += height_row + 1
    return readEncode(img)


def computeRowSize(img):
    """
    Compute the size of a row in manyImages2OneImage
    :param list img: List of images
    :returns: height, width
    :rtype: int, int
    """
    height = 0
    width = 0
    for i in img:
        h, w = i.shape[:2]
        width += w
        if h > height:
            height = h
    return height, width


def check_file(name):
    """
    Check the name of a file.
    return 1 if it is a tiff or a pdf and 0 otherwise.

    This function can be upgraded in order to include other
    format (1 for file, 2 for archive, 0 for not supported).
    In order to have a nice code, one should add the function
    is... when adding a new format

    :param str name: Name of the file to check
    :return: 1 if pdf or tiff, 2 if zip, 0 otherwise
    :rtype: int
    """
    if isPDF(name) or isTIFF(name):
        return 1
    elif isZIP(name):
        return 2
    else:
        return 0


def isPDF(name):
    """
    Check the extension of the name

    :param string name: File name to check
    :returns: True if PDF, False otherwise
    :rtype: bool
    """
    ext = os.path.splitext(name)[1]
    return (ext.lower() == '.pdf')


def isTIFF(name):
    """
    Check the extension of the name

    :param string name: File name to check
    :returns: True if TIFF, False otherwise
    :rtype: bool
    """
    ext = os.path.splitext(name)[1]
    return (ext.lower() == '.tif' or ext.lower() == '.tiff')


def isPNG(name):
    """
    Check the extension of the name

    :param string name: File name to check
    :returns: True if PNG, False otherwise
    :rtype: bool
    """
    ext = os.path.splitext(name)[1]
    return (ext.lower() == '.png')


def isZIP(name):
    """
    Check the extension of the name

    :param string name: File name to check
    :returns: True if ZIP, False otherwise
    :rtype: bool
    """
    ext = os.path.splitext(name)[1]
    return (ext.lower() == '.zip')


def read_csv(csv_file):
    """
    Reads a .csv file and returns its content as a list of dicts.

    Just like in csv.reader, csv_file can be any object which supports the
    iterator protocol and returns a string each time its next method is called.
    File objects and list objects are both suitable.
    """
    file_list = []
    reader = csv.reader(csv_file)
    header = reader.next()
    for row in reader:
        values = {}
        for key, value in zip(header, row):
            values[key] = value
        file_list.append(values)
    return file_list
