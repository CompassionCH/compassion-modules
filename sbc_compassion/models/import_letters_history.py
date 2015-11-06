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
This file reads a zip file containing scans of mail and find the relation
between the database and the mail.
"""
import cv2
import base64
import zipfile
import time
import shutil
import numpy as np
import os
from wand.image import Image

from ..tools import import_letter_functions as func
from ..tools import zxing
from ..tools import bluecornerfinder as bcf
from ..tools import checkboxreader as cbr
from ..tools import patternrecognition as pr
from openerp import api, fields, models, _, exceptions


# key to save in sponsorship_correspondence
key = ['partner_codega', 'name', 'template_id', 'letter_image',
       'is_encourager', 'supporter_languages_id', 'child_code',
       'sponsorship_id']


class ImportLettersHistory(models.Model):
    """
    Keep an history of the importation of letters.
    This class allows the user to import some letters (individually or in a
    zip) in the database by doing an automatic analysis.
    The code is reading some barcodes (QR code) in order to do the analysis
    (with the help of the library zxing)
    """
    _name = "import.letters.history"
    _description = _("""History of the letters imported Import mail from a zip
    or a PDF/TIFF""")

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    _order = "create_date"
    state = fields.Selection([
        ("draft", _("Draft")),
        ("pending", _("Pending")),
        ("ready", _("Ready to be saved")),
        ("saved", _("Saved"))], compute="_set_ready")
    nber_letters = fields.Integer(_('Number of letters'), readonly=True,
                                  compute="_count_nber_letters")
    # path where the zipfile are store
    path = "/tmp/sbc_compassion/"
    # list zip in the many2many
    # use ';' in order to separate the files
    list_zip = fields.Text("LIST_ZIP", readonly=True)

    data = fields.Many2many('ir.attachment', string=_("Add a file"))
    letters_line_ids = fields.Many2many('import.letter.line')
    letters_ids = fields.Many2many('sponsorship.correspondence')

    @api.one
    @api.depends("letters_line_ids", "letters_line_ids.status",
                 "letters_ids", "data")
    def _set_ready(self):
        check = True
        for i in self.letters_line_ids:
            if i.status != "ok":
                check = False
        if check and len(self.letters_line_ids) > 0:
            self.state = "ready"
        elif len(self.letters_ids) > 0:
            self.state = "saved"
        elif len(self.letters_line_ids) > 0:
            self.state = "pending"
        else:
            self.state = "draft"

    @api.model
    def create(self, vals):
        result = super(models.Model, self).create(vals)
        result._run_analyze()
        return result

    @api.multi
    @api.onchange("data", "letters_line_ids", "letters_ids")
    def _count_nber_letters(self):
        """
        Counts the number of scans (if a zip is given, count the number
        inside it)
        """
        for inst in self:
            if inst.state == "pending" or inst.state == "ready":
                inst.nber_letters = len(inst.letters_line_ids)
            elif inst.state == "saved":
                inst.nber_letters = len(inst.letters_ids)
            elif inst.state is False or inst.state == "draft":
                if inst.list_zip is False:
                    inst.list_zip = ""
                # removes old files in the directory
                if os.path.exists(inst.path):
                    onlyfiles = [f for f in os.listdir(inst.path)]
                    # loop over files
                    for f in onlyfiles:
                        t = time.time()
                        t -= os.path.getctime(inst.path + f)
                        # if file older than 12h
                        if t > 43200:
                            if os.path.isfile(f):
                                os.remove(f)
                            if os.path.isdirectory(f):
                                shutil.rmtree(f)
                else:
                    os.makedirs(inst.path)

                # counter
                tmp = 0
                # loop over all the attachments
                for attachment in inst.data:
                    # pdf or tiff case
                    if func.check_file(attachment.name) == 1:
                        tmp += 1
                    # zip case
                    elif func.isZIP(attachment.name):
                        tmp_name_file = inst.path + attachment.name
                        # save the zip file
                        if not os.path.exists(tmp_name_file):
                            f = open(tmp_name_file, 'w')
                            f.write(base64.b64decode(attachment.with_context(
                                bin_size=False).datas))
                            f.close()
                            if attachment.name not in inst.list_zip:
                                inst.list_zip = func.addname(inst.list_zip,
                                                             attachment.name)
                                # catch ALL the exceptions that can be raised
                                # by class zipfile
                                try:
                                    zip_ = zipfile.ZipFile(tmp_name_file, 'r')
                                except zipfile.BadZipfile:
                                    raise exceptions.Warning(
                                        _('Zip file corrupted (' +
                                          attachment.name + ')'))
                                except zipfile.LargeZipFile:
                                    raise exceptions.Warning(
                                        _('Zip64 is not supported(' +
                                          attachment.name + ')'))
                            list_file = zip_.namelist()
                            # loop over all files in zip
                            for tmp_file in list_file:
                                tmp += (func.check_file(tmp_file) == 1)
                inst.nber_letters = tmp
                # deletes zip removed from the data
                for f in inst.list_zip.split(';'):
                    if f not in inst.mapped('data.name') and f != '':
                        if os.path.exists(inst.path + f):
                            tmp = func.removename(inst.list_zip, f)
                            if tmp == -1:
                                raise exceptions.Warning(
                                    _("""Does not find the file
                                    during suppression"""))
                            else:
                                inst.list_zip = tmp
                            os.remove(inst.path + f)
            else:
                raise exceptions.Warning(
                    _("State: '{}' not implemented".format(inst.state)))

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _run_analyze(self):
        """
        Analyze each attachment (decompress zip too) by checking if the file
        is not done twice (check same name)[, extract zip], use
        analyze_attachment at the end
        """
        for inst in self:
            # list for checking if a file come twice
            check = []
            for attachment in inst.data:
                if attachment.name not in check:
                    check.append(attachment.name)
                    # check for zip
                    if func.check_file(attachment.name) == 2:
                        zip_ = zipfile.ZipFile(
                            inst.path + attachment.name, 'r')

                        path_zip = inst.path + os.path.splitext(
                            str(attachment.name))[0]

                        if not os.path.exists(path_zip):
                            os.makedirs(path_zip)
                        for f in zip_.namelist():
                            zip_.extract(f, path_zip)
                            absname = path_zip + '/' + f
                            if os.path.isfile(absname):
                                # remove if PDF is working
                                if func.isPDF(absname):
                                    raise exceptions.Warning(
                                        _("PDF not implemented yet"))
                                inst._analyze_attachment(absname)
                        # delete all the tmp files
                        # extracted data
                        shutil.rmtree(path_zip)
                        # zip file
                        os.remove(inst.path + attachment.name)
                    # case with normal format ([PDF,]TIFF)
                    elif func.check_file(attachment.name) == 1:
                        # remove if PDF is working
                        if func.isPDF(attachment.name):
                            raise exceptions.Warning(
                                _("PDF not implemented yet"))
                        inst._analyze_attachment(
                            inst.path + str(attachment.name),
                            attachment.datas)
                    else:
                        raise exceptions.Warning(
                            'Still a file in a non-accepted format')
                else:
                    raise exceptions.Warning(_('Two files are the same'))
            # remove all the files (now there are inside import_line_ids)
            for attachment in inst.data:
                attachment.unlink()

    def _analyze_attachment(self, file_, data=None):
        """
        Analyze attachment (PDF/TIFF) and save everything inside
        import_line_ids.

        :param string file_: Name of the file to analyze
        :param binary data: Image to scan (by default, read it from hdd)
        """
        # in the case of zipfile, the data needs to be saved first
        if data is not None:
            f = open(file_, 'w')
            f.write(base64.b64decode(data))
            f.close()

        # convert to PNG
        if func.isPDF(file_) or func.isTIFF(file_):
            if data is None:
                f = open(file_)
                data = f.read()
            name = os.path.splitext(file_)[0]
            with Image(filename=file_) as img:
                img.format = 'png'
                img.save(filename=name + '.png')
            os.remove(file_)
            file_ = name + '.png'

        # now do the computations only if the image is a PNG
        img = cv2.imread(file_)
        if func.isPNG(file_):
            # first compute the QR code
            zx = zxing.BarCodeTool()
            qrcode = zx.decode(file_, try_harder=True)
            if qrcode is not None and 'XX' in qrcode.data:
                partner, child = qrcode.data.split('XX')
            else:
                partner = None
                child = None
            # now try to find the layout
            # loop over all the patterns in the pattern directory
            template, key_img = self._find_template(img)
            lang_id = self._find_language(img, key_img, template)

            # TODO
            #
            # Problem: the converted jpeg can be opened on a windows PC or
            # with nano, but odoo can't recognize the file. Tried
            # to give a jpeg
            # to odoo from windows -> same problem

            letters_line = self.env['import.letter.line'].create({
                'partner_codega': partner,
                'child_code': child,
                'is_encourager': False,
                'supporter_languages_id': lang_id,
                'template_id': template.id,
            })

            file_png = open(file_, "r")
            file_data = file_png.read()
            file_png.close()
            dfile_ = file_.split('/')[-1]
            document_vals = {'name': dfile_,
                             'datas': data,
                             'datas_fname': dfile_,
                             'res_model': 'import.letter.line',
                             'res_id': letters_line.id
                             }
            letters_line.letter_image = self.env[
                'ir.attachment'].create(document_vals)
            letters_line.letter_image_preview = base64.b64encode(file_data)

            self.letters_line_ids += letters_line

        else:
            raise exceptions.Warning('Format not accepted in {}'.format(file_))

    def _find_template(self, img):
        """
        Use the pattern recognition in order to recognize the layout.
        The template used for the pattern recognition are taken from
        the directory ../tools/pattern/
        :param array file_: Image to analyze
        :returns: Pattern image of the template, keypoint of the image
        :rtype: str, list
        """
        template_obj = self.env['sponsorship.correspondence.template']
        # number of keypoint related between the picture and the pattern
        nber_kp = 0
        key_img = False
        matching_template = self.env.ref('sbc_compassion.default_template')

        for template in template_obj.search([('pattern_image', '!=', False)]):
            # Crop the image to speedup detection and avoid false positives
            crop_area = template.get_pattern_area()

            # try to recognize the pattern
            tmp_key = pr.patternRecognition(
                img, template.pattern_image, crop_area)
            # check if it is a better result than before
            if tmp_key is not None and len(tmp_key) > nber_kp:
                # save all the data if it is better
                nber_kp = len(tmp_key)
                key_img = tmp_key
                matching_template = template

            return matching_template, key_img

    def _find_language(self, img, key_img, template):
        """
        Use the pattern and the blue corner for doing a transformation
        (rotation + scaling + translation) in order to crop a small part
        of the original picture around the position of each languages.
        The rotation matrix is given by R, the scaling one by scaling
        and the translation by C.
        The rotation angle :math:`\theta` is given by the angle between
        the template and image vectors that start from the blue square (B)
        and end at the pattern.
        The scaling is given in a matrix form where math:`S_1` is the
        ratio between the width of the image and the one of the template
        (same for the height with :math:`S_2`)
        The translation vector is construct with the two previous matrices
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
        This analysis should be quite fast due to the small size of
        pictures to analyze (should be a square of about 20-30 pixels large).

        :param img: Image to analyze
        :param list key_img: List containing the keypoint detected
        :param CorrespondenceTemplate template: Template of the image
        :returns: Language of the letter (defined in Layout, returns None if \
        not detected)
        :rtype: str or bool
        """
        # create an instance of layout (contains all the information)
        # about the position
        center_pat = pr.keyPointCenter(key_img)
        # in case of not being able to detect the pattern
        if center_pat is None:
            return
        # get position of the blue corner
        bluecorner = bcf.BlueCornerFinder(img)
        bluecorner_position = bluecorner.getIndices()

        # vector between the blue square and the pattern
        diff_ref = np.array(template.get_bluesquare_area() -
                            template.get_pattern_center())
        diff_scan = np.array(bluecorner_position-center_pat)
        # need normalize vectors
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
        # check if only 1 language is find
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

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def button_save(self):
        """
        save the import_line as a sponsorship_correspondence
        TODO
        """
        test = True
        for inst in self:
            if inst.state != "ready":
                test = False
        if test is False:
            raise exceptions.Warning(_("Not all data are OK"))

        for inst in self:
            for letter in inst.letters_line_ids:
                data = {}
                for i in key:
                    data[i] = letter.read()[0][i]
                inst.letters_ids.write(data)
            for letter in inst.letters_line_ids:
                letter.unlink()
