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
import subprocess
import os
import shutil
import pdb
import PythonMagick
import sys
import numpy as np
sys.path.append(os.path.abspath(os.path.dirname(__file__)+'/../tools'))
from import_mail_functions import *
import bluecornerfinder as bcf
import checkboxreader as cbr
import patternrecognition as pr
import positionpattern as pp
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
        if isPDF(file_) or isTIFF(file_):
            # convert
            name = os.path.splitext(file_)[0]
            image = PythonMagick.Image()
            image.density("300")
            image.read(file_)
            image.write(name + '.png')
            os.remove(file_)
            file_ = name + '.png'
        if isPNG(file_):
            try:
                zx = zxing.BarCodeTool()
                code = zx.decode(file_,try_harder=True)
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
                    _("Barcode ({0}) not in the required format in file: {1}"
                  ).format(code.data,file_))

            path = os.path.dirname(__file__)+'/../tools/pattern/'
            listing = os.listdir(os.path.abspath(path))
            a = 0
            for f in listing:
                box = np.array(pp.pattern_pos,float)
                box[:2] = box[:2]/float(pp.size_ref[0])
                box[2:] = box[2:]/float(pp.size_ref[1])
                
                tmp_key = pr.patternRecognition(
                    file_,path+f,box=([box[0],box[1]],[box[2],box[3]]))
                if tmp_key != None and len(tmp_key[0]) > a:
                    a = len(tmp_key[0])
                    kimg = tmp_key[0]
                    ktemp = tmp_key[1]
                    pattern_file = os.path.splitext(f)[0]
            ctemp = pr.keyPointCenter(kimg)
            
            bluecorner = bcf.BlueCornerFinder(file_)
            cblue = bluecorner.getIndices()
            
            diff_ori = np.array(pp.pattern['bluesquare']-
                                pp.pattern[pattern_file])
            diff_scan = np.array(cblue-ctemp)
            normalization = (np.linalg.norm(diff_ori)*
                             np.linalg.norm(diff_scan))
            costheta = np.dot(diff_ori,diff_scan)/normalization
            sintheta = np.linalg.det([diff_ori,diff_scan])/normalization
            
            M = np.array([[costheta, -sintheta],[sintheta, costheta]])
            
            scaling = np.array(bluecorner.getSizeOriginal(),dtype=float) \
                      /np.array(pp.size_ref,dtype=float)
            scaling = np.array([[scaling[0],0],[0,scaling[1]]])
            M *= scaling
            
            C = cblue-np.dot(M,np.array(pp.pattern['bluesquare']))
            
            img = cv2.imread('/home/openerp/layout_test.png')
            i = pp.checkboxes
            
            #co = cimg2
            
            for key in pp.checkboxes:
                w,h = bluecorner.getSizeOriginal()
                x,y = img.shape[:2]
                a = i[key][2]*x/h
                b = i[key][3]*x/h
                (a,b) = np.round(np.dot(M,np.array([a,b])) + C)
                c = i[key][0]*y/w
                d = i[key][1]*y/w
                (c,d) = np.round(np.dot(M,np.array([c,d])) + C)
                cv2.imwrite('/home/openerp/check_'+key+'.png',img[a:b+1,c:d+1])
                
                
            A = cbr.CheckboxReader('/home/openerp/check_other.png')               
            
            """except:
                raise exceptions.Warning(
                    _("Unable to detect patterns in : {}").format(
                        file_))
               """ 

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

            image = PythonMagick.Image(file_)
            image.write(f_tmp)

            import_mail_line = self.env['import.mail.line'].create({
                'partner_codega': partner,
                'child_code': child,
                'is_encourager': False,
                'supporter_languages_id': False,
                'template_id': 'template_1',
                'status': 'ok'})
            
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
