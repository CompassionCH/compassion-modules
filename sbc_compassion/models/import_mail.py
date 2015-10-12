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

import base64
import zipfile
import time
import subprocess
import os
import shutil
import pdb
import PythonMagick
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)+'/../tools'))
from import_mail_functions import *
from openerp import api, fields, models, _, exceptions
# import sponsorship_correspondence

import zxing

class ImportMail(models.TransientModel):

    """
    Model for Import mail
    This class allows the user to import some letters (individually or in a
    zip) in the database by doing an automatic analysis.
    The code is reading some barcodes (QR code) in order to do the analysis
    (with the help of the library zxing)
    """
    _name = "import.mail"
    _description = _("Import mail from a zip or a PDF/TIFF")

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    nber_file = fields.Integer(_('Number of files: '), readonly=True,
                               compute="_count_nber_files")
    title = fields.Text(_("Import Mail"), readonly=True)
    debug = fields.Text("DEBUG", readonly=True)
    # path where the zipfile are store
    path = "/tmp/sbc_compassion/"
    # list zip in the many2many
    # use ';' in order to separate the files
    list_zip = fields.Text("LIST_ZIP", readonly=True)

    # link to _count_nber_files
    data = fields.Many2many('ir.attachment')
    import_mail_line_ids = fields.Many2many('import.mail.line')

    # -------------------- _COUNT_NBER_FILES ---------------------------------

    @api.one
    @api.onchange("data")
    def _count_nber_files(self):
        """
        Counts the number of scans (if a zip is given, count the number
        inside it)
        """
        if self.list_zip is False:
            self.list_zip = ""
        if self.debug is False:
            self.debug = "YOUPI"
        # removes old files in the directory
        if os.path.exists(self.path):
            onlyfiles = [f for f in os.listdir(self.path)
                         if os.path.isfile(os.path.join(self.path, f))]
            # loop over files
            for f in onlyfiles:
                t = time.time()
                t -= os.path.getctime(self.path + f)
                # if file older than 12h
                if t > 43200:
                    os.remove(f)
        else:
            os.makedirs(self.path)

        # counter
        tmp = 0
        # loop over all the attachments
        for attachment in self.data:
            # pdf or tiff case
            if check_file(attachment.name) == 1:
                tmp += 1
            # zip case
            elif check_file(attachment.name) == 2:
                tmp_name_file = self.path + attachment.name
                # save the zip file
                if not os.path.exists(tmp_name_file):
                    f = open(tmp_name_file, 'w')
                    f.write(base64.b64decode(attachment.with_context(
                        bin_size=False).datas))
                    f.close()
                    if attachment.name not in self.list_zip:
                        self.list_zip = addname(self.list_zip, attachment.name)
                # catch ALL the exceptions that can be raised by class
                # zipfile
                try:
                    zip_ = zipfile.ZipFile(tmp_name_file, 'r')
                except zipfile.BadZipfile:
                    raise exceptions.Warning(_('Zip file corrupted (' +
                                               attachment.name + ')'))
                except zipfile.LargeZipFile:
                    raise exceptions.Warning(_('Zip64 is not supported(' +
                                               attachment.name + ')'))
                else:
                    list_file = zip_.namelist()
                    # loop over all files in zip
                    for tmp_file in list_file:
                        tmp += check_file(tmp_file)
        self.nber_file = tmp
        # deletes zip removed from the data
        for f in self.list_zip.split(';'):
            if f not in self.mapped('data.name') and f != '':
                if os.path.exists(self.path + f):
                    tmp = removename(self.list_zip, f)
                    if tmp == -1:
                        raise exceptions.Warning(
                            _("Does not find the file during suppression"))
                    else:
                        self.list_zip = tmp
                    os.remove(self.path + f)

    # ------------------------ _RUN_ANALYZE ----------------------------------

    @api.one
    def button_run_analyze(self):
        """
        Analyze each attachment (decompress zip too) by checking if the file
        is not done twice (check same name)[, extract zip], use
        analyze_attachment at the end

        """
        # list for checking if a file come twice
        check = []
        for attachment in self.data:
            if attachment.name not in check:
                check.append(attachment.name)
                # check for zip
                if check_file(attachment.name) == 2:
                    zip_ = zipfile.ZipFile(self.path + attachment.name, 'r')
                    path_zip = self.path + os.path.splitext(
                        str(attachment.name))[0]
                    if not os.path.exists(path_zip):
                        os.makedirs(path_zip)
                    for f in zip_.namelist():
                        zip_.extract(f, path_zip)
                        absname = path_zip + '/' + f
                        if os.path.isfile(absname):
                            self.analyze_attachment(absname)
                    # delete all the tmp files
                    shutil.rmtree(path_zip)
                    os.remove(self.path + attachment.name)
                # case with normal format (PDF,TIFF)
                elif check_file(attachment.name) == 1:
                    self.analyze_attachment(
                        self.path + str(attachment.name),
                        attachment.datas)
                    os.remove(self.path + attachment.name)
                else:
                    raise exceptions.Warning(
                        'Still a file in a non-accepted format')
                    return
            else:
                raise exceptions.Warning(_('Two files are the same'))
                return

    def analyze_attachment(self, file_, data=None):
        """
        Analyze attachment (PDF/TIFF) and save everything

        :param string file_: Name of the file to analyze
        :param binary data: Image to scan (by default, read it from hdd)
        :returns: Barcode (error code: 1 was not able to read it, 2 format\
                  not accepted)
        :rtype: String (error code: int)
        """
        if data is not None:
            f = open(file_, 'w')
            f.write(base64.b64decode(data))
            f.close()
        if isPDF(file_):
            # convert
            name = os.path.splitext(file_)[0]
            cmd = ['convert', file_, file_ + '.tif']
            (stdout, stderr) = subprocess.Popen(
                cmd, stdout=subprocess.PIPE,
                universal_newlines=True).communicate()
            os.remove(file_)
            file_ = name + '.tif'
        if isTIFF(file_) or isPDF(file_):
            try:
                zx = zxing.BarCodeTool()
                code = zx.decode(file_)
            except:
                raise exceptions.Warning(
                    _("Unable to read file: {}").format(file_))
            if code is None:
                raise exceptions.Warning(
                    _("Not able to read barcode from: {}").format(file_))
            try:
                partner, child = code.data.split('XX')
            except:
                raise exceptions.Warning(
                    _("Barcode not in the required format in file: {}").format(
                        file_))

            # NEED REVIEW
            #
            # template_id
            # supporter_language (method needed for check if partner langage
            # exist in res.lang.compassion / field have to be set required in
            # import.mail.line)
            # status (local variable with status selection needed, please
            # refer to the status selection field)
            #
            # Problem: the converted jpeg can be opened on a windows PC or
            # with nano, but odoo can't recognize the file. Tried
            # to give a jpeg
            # to odoo from windows -> same problem

            f_tmp = os.path.splitext(file_)[0] + ".jpeg"

            cmd = ['convert', file_, f_tmp]
            (stdout, stderr) = subprocess.Popen(
                cmd, stdout=subprocess.PIPE,
                universal_newlines=True).communicate()

            import_mail_line = self.env['import.mail.line'].create({
                'partner_codega': partner,
                'child_code': child,
                'is_encourager': False,
                'supporter_languages_id': False,
                'template_id': 'template_1',
                'status': 'ok'})
            pdb.set_trace()
            file_jpeg = open(f_tmp, "r")
            document_vals = {'name': 'file_.jpeg',
                             'datas': file_jpeg.read(),
                             'datas_fname': 'file_.jpeg',
                             'res_model': 'import.mail.line',
                             'res_id': import_mail_line.id
                             }

            image = self.env['ir.attachment'].create(document_vals)
            import_mail_line.letter_image_preview = image
            file_jpeg.close()

            self.import_mail_line_ids += import_mail_line

        else:

            raise exceptions.Warning('Format not accepted in {}'.format(file_))
