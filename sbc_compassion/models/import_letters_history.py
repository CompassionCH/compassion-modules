# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Mathier <emmanuel.mathier@gmail.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
"""
This module reads a zip file containing scans of mail and finds the relation
between the database and the mail.
"""
import cv2
import base64
import zipfile
import numpy as np
import os
from wand.image import Image
import tempfile
import shutil
from glob import glob

from ..tools import import_letter_functions as func
from ..tools import zxing
from ..tools import bluecornerfinder as bcf
from ..tools import checkboxreader as cbr
from ..tools import patternrecognition as pr
from openerp import api, fields, models, _, exceptions


class ImportLettersHistory(models.Model):
    """
    Keep history of imported letters.
    This class allows the user to import some letters (individually or in a
    zip file) in the database by doing an automatic analysis.
    The code is reading QR codes in order to detect child and partner codes
    for every letter, using the zxing library for code detection.
    """
    _name = "import.letters.history"
    _description = _("""History of the letters imported Import mail from a zip
    or a PDF/TIFF""")
    _order = "create_date desc"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    state = fields.Selection([
        ("draft", _("Draft")),
        ("open", _("Open")),
        ("ready", _("Ready")),
        ("done", _("Done"))], compute="_set_ready")
    nber_letters = fields.Integer(
        'Number of letters', readonly=True, compute="_count_nber_letters")
    is_mandatory_review = fields.Boolean(
        'Mandatory Review',
        states={'done': [('readonly', True)]})
    data = fields.Many2many('ir.attachment', string="Add a file")
    import_line_ids = fields.One2many(
        'import.letter.line', 'import_id', 'Files to process')
    letters_ids = fields.One2many(
        'sponsorship.correspondence', 'import_id', 'Imported letters',
        readonly=True)
    force_template = fields.Many2one('sponsorship.correspondence.template',
                                     'Force Template')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    @api.depends("import_line_ids", "import_line_ids.status",
                 "letters_ids", "data")
    def _set_ready(self):
        """ Check in which state self is by counting the number of elements in
        each Many2many
        """
        for import_letters in self:
            if import_letters.letters_ids:
                import_letters.state = "done"
            elif import_letters.import_line_ids:
                check = True
                for i in import_letters.import_line_ids:
                    if i.status != "ok":
                        check = False
                if check:
                    import_letters.state = "ready"
                else:
                    import_letters.state = "open"
            else:
                import_letters.state = "draft"

    @api.multi
    @api.onchange("data", "import_line_ids", "letters_ids")
    def _count_nber_letters(self):
        """
        Counts the number of scans. If a zip file is given, the number of
        scans inside is counted.
        """
        for inst in self:
            if inst.state == "open" or inst.state == "ready":
                inst.nber_letters = len(inst.import_line_ids)
            elif inst.state == "done":
                inst.nber_letters = len(inst.letters_ids)
            elif inst.state is False or inst.state == "draft":
                # counter
                tmp = 0
                # loop over all the attachments
                for attachment in inst.data:
                    # pdf or tiff case
                    if func.check_file(attachment.name) == 1:
                        tmp += 1
                    # zip case
                    elif func.isZIP(attachment.name):
                        # create a tempfile and read it
                        with tempfile.NamedTemporaryFile(
                                suffix='.zip') as zip_file:
                            zip_file.write(base64.b64decode(
                                attachment.with_context(
                                    bin_size=False).datas))
                            zip_file.flush()
                            # catch ALL the exceptions that can be raised
                            # by class zipfile
                            try:
                                zip_ = zipfile.ZipFile(zip_file.name, 'r')
                                list_file = zip_.namelist()
                                # loop over all files in zip
                                for tmp_file in list_file:
                                    tmp += (func.check_file(tmp_file) == 1)
                            except zipfile.BadZipfile:
                                raise exceptions.Warning(
                                    _('Zip file corrupted (' +
                                      attachment.name + ')'))
                            except zipfile.LargeZipFile:
                                raise exceptions.Warning(
                                    _('Zip64 is not supported(' +
                                      attachment.name + ')'))

                inst.nber_letters = tmp
            else:
                raise exceptions.Warning(
                    _("State: '{}' not implemented".format(inst.state)))

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def button_import(self):
        for letters_import in self:
            if letters_import.data:
                letters_import._run_analyze()
        return True

    @api.multi
    def button_save(self):
        """
        save the import_line as a sponsorship_correspondence
        """
        # check if all the imports are OK
        for letters_h in self:
            if letters_h.state != "ready":
                raise exceptions.Warning(_("Some letters are not ready"))
        # save the imports
        for letters in self:
            ids = letters.import_line_ids.get_letter_datas(
                mandatory_review=letters.is_mandatory_review)
            # letters_ids should be empty before this line
            letters.write({'letters_ids': ids})
            letters.import_line_ids.letter_image.unlink()
            letters.import_line_ids.unlink()
        return True

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _run_analyze(self):
        """
        Analyze each attachment:
        - check for duplicate file names and skip them
        - decompress zip file if necessary
        - call _analyze_attachment for every resulting file
        """
        self.ensure_one()
        # keep track of file names to detect duplicates
        file_name_history = []
        for attachment in self.data:
            if attachment.name not in file_name_history:
                file_name_history.append(attachment.name)
                # check for zip
                if func.check_file(attachment.name) == 2:
                    # create a temp file
                    with tempfile.NamedTemporaryFile(
                            suffix='.zip') as zip_file:
                        # write data in tempfile
                        zip_file.write(base64.b64decode(
                            attachment.with_context(
                                bin_size=False).datas))
                        zip_file.flush()
                        zip_ = zipfile.ZipFile(
                            zip_file, 'r')
                        # loop over files inside zip
                        directory = tempfile.mkdtemp()
                        for f in zip_.namelist():
                            zip_.extract(
                                f, directory)
                            absname = directory + '/' + f
                            if os.path.isfile(absname):
                                # remove if PDF is working
                                if func.isPDF(absname):
                                    raise exceptions.Warning(
                                        _("PDF not implemented yet"))
                                filename = f.split('/')[-1]
                                self._analyze_attachment(absname,
                                                         filename)
                        shutil.rmtree(directory)
                # case with normal format ([PDF,]TIFF)
                elif func.check_file(attachment.name) == 1:
                    # remove if PDF is working
                    if func.isPDF(attachment.name):
                        raise exceptions.Warning(
                            _("PDF not implemented yet"))
                    ext = os.path.splitext(attachment.name)[1]
                    with tempfile.NamedTemporaryFile(
                            suffix=ext) as file_:
                        file_.write(base64.b64decode(
                            attachment.with_context(
                                bin_size=False).datas))
                        file_.flush()
                        self._analyze_attachment(file_.name,
                                                 attachment.name)
                else:
                    raise exceptions.Warning(
                        'Still a file in a non-accepted format')
            else:
                raise exceptions.Warning(_('Two files are the same'))
        # remove all the files (now they are inside import_line_ids)
        self.data.unlink()

    def _analyze_attachment(self, file_, filename):
        """
        Analyze attachment (PDF/TIFF) and save everything inside
        import_line_ids.
        The filename is given separately due to the name given by tempfile

        :param str file_: Path of the file to analyze
        :param str filename: Filename to give in odoo
        """
        f = open(file_)
        data = f.read()
        f.close()
        # convert to PNG
        if func.isPDF(file_) or func.isTIFF(file_):
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
        line_vals, data, img = self._find_qrcode(img, MULTIPAGE, file_, data)

        # now try to find the layout
        # loop over all the patterns in the pattern directory
        template, pattern_center = self._find_template(img)
        lang_id = self._find_language(img, pattern_center, template)

        if self.force_template:
            template = self.force_template

        line_vals.update({
            'is_encourager': False,
            'supporter_languages_id': lang_id,
            'template_id': template.id,
        })
        letters_line = self.env['import.letter.line'].create(line_vals)

        file_png_io = open(file_png, "r")
        file_data = file_png_io.read()
        file_png_io.close()

        document_vals = {'name': filename,
                         'datas': base64.b64encode(data),
                         'datas_fname': filename,
                         'res_model': 'import.letter.line',
                         'res_id': letters_line.id}

        letters_line.letter_image = self.env[
            'ir.attachment'].create(document_vals)
        letters_line.letter_image_preview = base64.b64encode(file_data)

        self.import_line_ids += letters_line
        os.remove(file_png)
        if MULTIPAGE:
            delfiles = glob(name + '*png')
            for file_ in delfiles:
                os.remove(file_)

    def _find_qrcode(self, img, MULTIPAGE, file_,
                     data):
        """
        Read the image and try to find the QR code.
        The image should be currently saved as a png with the same name
        than file_ (except for the extension).
        Data is given in order to give the possibility to overwrite it when
        the file is scanned in the wrong direction.

        :param np.array img: Image to analyze
        :param bool MULTIPAGE: If the file is multipage
        :param file_: Name of the temporary file
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
            self.env['ir.config_parameter'].get_param(
                'qrcode_x_min'))
        top = img_height * float(
            self.env['ir.config_parameter'].get_param(
                'qrcode_y_min'))
        width = img_width * float(
            self.env['ir.config_parameter'].get_param(
                'qrcode_x_max'))
        width -= left
        height = img_height * float(
            self.env['ir.config_parameter'].get_param(
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
            # save it for zxing
            cv2.imwrite(file_png, img)
            # second attempt
            qrcode = zx.decode(file_png, try_harder=True, crop=[
                int(left), int(top), int(width), int(height)])
            # if the QR code is found
            if qrcode is not None:
                # replace the image by the returned one
                data = self._save_img(MULTIPAGE, file_, img)
        if qrcode is not None and 'XX' in qrcode.data:
            partner_id, child_id = qrcode.data.split('XX')
            child_id = self.env['compassion.child'].search(
                [('code', '=', child_id)]).id
            partner_id = self.env['res.partner'].search(
                [('ref', '=', partner_id)]).id

        else:
            partner_id = None
            child_id = None

        dict_odoo = {
            'partner_id': partner_id,
            'child_id': child_id,
        }
        return dict_odoo, data, img

    def _save_img(self, MULTIPAGE, file_, img):
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

    def _find_template(self, img):
        """
        Use pattern recognition to detect which template corresponds to img.
        :param img: Image to analyze
        :returns: Detected template, center position of detected pattern
        :rtype: template, layout
        """
        templates = self.env['sponsorship.correspondence.template'].search(
            [('pattern_image', '!=', False)])
        return pr.find_template(img, templates)

    def _find_language(self, img, pattern_center, template):
        """
        Use the pattern and the blue corner for doing a transformation
        (rotation + scaling + translation) in order to crop a small part
        of the original picture around the position of each language
        check box.
        The rotation matrix is given by R, the scaling one by scaling
        and the translation by C.
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

        :param img: Image to analyze
        :param pattern_center: Center position of detected pattern
        :param CorrespondenceTemplate template: Template of the image
        :returns: Language of the letter (defined in Layout, returns None if \
        not detected)
        :rtype: str or bool
        """
        # if pattern has not been detected
        if pattern_center is None:
            return
        # get position of the blue corner
        bluecorner = bcf.BlueCornerFinder(img)
        bluecorner_position = bluecorner.getIndices()

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

        # now for the language

        # language
        lang = False
        # check if only 1 language was found
        lang_ok = True
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
            A = cbr.CheckboxReader(img[a:b+1, c:d+1])
            # if something happens
            # if A.test is True or A.getState is True or A.getState is None:
            if A.getState() is True:
                # if a second language has been discovered
                if lang is not False:
                    lang_ok = False
                else:
                    # change the value for odoo
                    lang = checkbox.language_id
        if lang and lang_ok:
            lang = lang.id
        else:
            lang = False
        return lang
