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
import os
import cv2
import base64
import zxing
import tempfile
import patternrecognition as pr
import checkboxreader as cbr
import bluecornerfinder as bcf
import numpy as np
from glob import glob
from wand.image import Image


##########################################################################
#                           GENERAL METHODS                              #
##########################################################################

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
    """
    f = open(file_)
    data = f.read()
    f.close()
    # convert to PNG
    if isPDF(file_) or isTIFF(file_):
        name = os.path.splitext(file_)[0]
        with Image(filename=file_) as img:
            img.format = 'png'
            img.save(filename=name + '.png')
        file_png = name + '.png'
    # now do the computations only if the image is a PNG
    img = cv2.imread(file_png)
    MULTIPAGE = False
    if img is None:
        file_png = name + '-0' + '.png'
        img = cv2.imread(file_png)
        MULTIPAGE = True
        if img is None:
            raise Warning("The '{}' image cannot be read".format(filename))
    # first compute the QR code
    line_vals, data, img = _find_qrcode(env, img, MULTIPAGE, file_, data, test)
    # now try to find the layout
    # loop over all the patterns in the pattern directory
    line_vals, pattern_center = _find_template(env, img, line_vals)
    if line_vals['template_id'] != env.ref('sbc_compassion.default_template'):
        line_vals = _find_languages(env, img, pattern_center, line_vals)
    else:
        line_vals.update({
            'letter_language_id': False
        })
    if force_template and force_template is not None:
        line_vals.update({
            'template_id': force_template.id
        })

    line_vals.update({
        'is_encourager': False,
    })
    letters_line = env['import.letter.line'].create(line_vals)

    file_png_io = open(file_png, "r")
    file_data = file_png_io.read()
    file_png_io.close()

    document_vals = {'name': filename,
                     'datas': base64.b64encode(data),
                     'datas_fname': filename,
                     'res_model': 'import.letter.line',
                     'res_id': letters_line.id}

    letters_line.letter_image = env[
        'ir.attachment'].create(document_vals)
    letters_line.letter_image_preview = base64.b64encode(file_data)

    os.remove(file_png)
    if MULTIPAGE:
        delfiles = glob(name + '*png')
        for file_ in delfiles:
            os.remove(file_)
    return letters_line


def _find_qrcode(env, img, MULTIPAGE, file_,
                 data, test):
    """
    Read the image and try to find the QR code.
    The image should be currently saved as a png with the same name
    than file_ (except for the extension).
    Data is given in order to give the possibility to overwrite it when
    the file is scanned in the wrong direction.
    In case of test, the output dictonnary contains the image of the QR code
    too.

    :param env env: Odoo variable env
    :param np.array img: Image to analyze
    :param bool MULTIPAGE: If the file is multipage
    :param file_: Name of the temporary file
    :param bool test: Save the image of the QR code or not
    :returns: {partner_id, child_id}, data, img
    :rtype: dict, str, np.array
    """
    name = os.path.splitext(file_)[0]
    file_png = name + '.png'
    if MULTIPAGE:
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
    # check if found, if not means that page is rotated
    if qrcode is None:
        # rotate image
        img = img[::-1, ::-1]
        # second attempt
        cv2.imwrite(file_png, img)
        qrcode = zx.decode(file_png, try_harder=True, crop=[
            int(left), int(top), int(width), int(height)])
        # if the QR code is found
        if qrcode is not None:
            # save it for zxing
            cv2.imwrite(file_png, img)
            # replace the image by the returned one
            data = _save_img(MULTIPAGE, file_, img)
        else:
            cv2.imwrite(file_png, img[::-1, ::-1])
            qrcode = zx.decode(file_png, try_harder=True)
    if qrcode is not None and 'XX' in qrcode.data:
        partner_id, child_id = qrcode.data.split('XX')
        child_id = env['compassion.child'].search(
            [('code', '=', child_id)]).id
        partner_id = env['res.partner'].search(
            [('ref', '=', partner_id),
             ('is_company', '=', False)]).id

    else:
        partner_id = None
        child_id = None

    dict_odoo = {
        'partner_id': partner_id,
        'child_id': child_id,
    }
    if test:
        right = int(left)+int(width)
        bottom = int(top) + int(height)
        test_img = cv2.imread(file_png)[int(top):bottom, int(left):right]
        with tempfile.NamedTemporaryFile(
                suffix='.png') as temp_file:
            cv2.imwrite(temp_file.name, test_img)
            f = open(temp_file.name)
            test_data = f.read()
            f.close()
        dict_odoo.update({
            'qr_preview': base64.b64encode(test_data)
        })
    return dict_odoo, data, img


def _save_img(MULTIPAGE, file_, img):
    """
    This method is called when an image is scanned in the wrong direction.
    It consists in saving the image (returning is already done before).
    In case of multipage, the pages need to be returned.

    :param bool MULTIPAGE: If the file is a multipage one
    :param str file_: Name of the file
    :param np.array img: Image
    :returns: Data contained in the file
    :rtype: str
    """
    # if multipage, needs to turn all of them
    name = os.path.splitext(file_)[0]
    if MULTIPAGE:
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


def _find_template(env, img, line_vals):
    """
    Use pattern recognition to detect which template corresponds to img.
    :param env env: Odoo variable env
    :param img: Image to analyze
    :param dict line_vals: Dictonnary containing the data for a line
    :returns: line_vals (updated), center position of detected pattern
    :rtype: dict, layout
    """
    templates = env['sponsorship.correspondence.template'].search(
        [('pattern_image', '!=', False)])
    threshold = float(
        env.ref('sbc_compassion.threshold_keypoints_template').value)
    template, pattern_center = pr.find_template(img, templates,
                                                threshold=threshold)
    if template is None:
        pattern_center = np.array(([0, 0], [0, 0]))
        template = env.ref('sbc_compassion.default_template')
    line_vals.update({
        'template_id': template
    })
    return line_vals, pattern_center


def _find_languages(env, img, pattern_center, line_vals):
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
    :returns: line_vals (updated)
    :rtype: dict
    """
    template = line_vals['template_id']
    # if pattern has not been detected
    if pattern_center is None:
        return []
    # get position of the blue corner
    box = [float(
        env['ir.config_parameter'].get_param('bluecorner_x_min')),
        float(
        env['ir.config_parameter'].get_param('bluecorner_y_max'))]
    bluecorner = bcf.BlueCornerFinder(img, box=box)
    bluecorner_position = bluecorner.getIndices()
    if bluecorner_position is None:
        return []

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
        # if something happens
        # if A.test is True or A.getState is True or A.getState is None:
        if A.getState() is True:
            lang.append(checkbox.language_id.id)
    if len(lang) == 1:
        lang = lang[0]
    else:
        lang = False
    line_vals.update({
        'letter_language_id': lang,
        'template_id': line_vals['template_id'].id
    })
    return line_vals


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
