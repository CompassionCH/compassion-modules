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
import os
import copy
import shutil
import pdb
from tempfile import TemporaryFile
import zxing
from openerp import api, fields, models, _, exceptions
import sponsorship_correspondance

def check_file(name):
    """
    Check the name of a file.
    return 1 if it is a tiff or a pdf and 0 otherwise.
    
    :param str name: Name of the file to check
    :return: 1 if pdf or tiff, 2 if zip, 0 otherwise
    :rtype: int
    """
    if (name[-4::].lower() in ['.pdf','.tif'] or  
        name[-5::].lower() == '.tiff'):
        return 1
    elif (name[-4::].lower() == '.zip'):
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
    if name[-4::].lower() == '.pdf':
        return True
    else:
        return False

def isTIFF(name):
    """
    Check the extension of the name

    :param string name: File name to check
    :returns: True if TIFF, False otherwise
    :rtype: bool
    """
    if (name[-4::].lower() == '.tif' or
        name[-5::].lower() == '.tiff'):
        return True
    else:
        return False
    

def isZIP(name):
    """
    Check the extension of the name

    :param string name: File name to check
    :returns: True if ZIP, False otherwise
    :rtype: bool
    """
    if (name[-4::].lower() == '.zip'):
        return True
    else:
        return False


def list2string(list_):
    """
    Transform a list to a string by separating the string in the list by ;

    :param [string] list_: List to transform
    :returns: Input list as a string and separated by ';'
    :rtype: String
    """
    tmp = ''
    for i in list_:
        tmp += i + ';'
    return tmp

def addname(string, name):
    """
    Add name to string by separating them with ;
    The name is put at the end of the string

    :param string string: String where to add the name
    :param string name: Name to add at the end of string
    """
    return string + name + ';'

def removename(string,name):
    """
    Find and remove name in string where string is a string separated with ;

    :param string string: String list separated by ';'
    :param string name: Name to find in string
    :returns: string without name or False
    :rtype: string or bool
    """
    i = string.find(name)
    if i == -1:
        return False
    else:
        return string[i:len(name)+1]



class ImportMail(models.TransientModel):
    """
    Model for Import mail
    This class allows the user to import some letters (individually or in a zip)
    in the database by doing an automatic analysis.
    The code is reading some barcodes (QR code) in order to do the analysis 
    (with the help of the library zxing)
    """
    _name = "import.mail"
    _description = _("Import mail from a zip or a PDF/TIFF")
    
    nber_file = fields.Integer(_('Number of files: '),readonly=True,
                               compute="_count_nber_files")
    title = fields.Text(_("Import Mail"),readonly=True)
    debug = fields.Text("DEBUG",readonly=True)
    # path where the zipfile are store
    path = "/tmp/sbc_compassion/"
    # list zip in the many2many
    # use ';' in order to separate the files
    list_zip = fields.Text("LIST_ZIP",select="")

    
    # link to _count_nber_files
    data = fields.Many2many('ir.attachment') 
    
    
    #-------------------- _COUNT_NBER_FILES ------------------------------------
    
    @api.one
    @api.onchange("data")
    def _count_nber_files(self):
        """
        Counts the number of scans (if a zip is given, count the number
        inside it)
        """
        if not self.list_zip:
            pdb.set_trace()
            self.list_zip = ""
        #removes old files in the directory
        if os.path.exists(self.path):
            onlyfiles = [ f for f in os.listdir(self.path)
                          if os.path.isfile(os.path.join(self.path,f)) ]
            # loop over files
            for f in onlyfiles:
                t = time.time()
                t -= os.path.getctime(self.path+f)
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
                tmp_name_file = self.path+attachment.name
                # save the zip file
                if not os.path.exists(tmp_name_file):
                    f = open(tmp_name_file,'w')
                    f.write(base64.b64decode(attachment.with_context(bin_size=False).datas))
                    f.close()
                    if attachment.name not in self.list_zip:
                        self.list_zip = addname(self.list_zip,attachment.name)
                # catch ALL the exceptions that can be raised by class
                # zipfile
                try:
                    zip_ = zipfile.ZipFile(tmp_name_file,'r')
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
                if os.path.exists(self.path+f):
                    tmp = removename(self.list_zip,f)
                    if tmp != -1:
                        raise exceptions.Warning(
                            _("I am not able to delete a file"))
                    else:
                        self.list_zip = tmp
                    os.remove(self.path+f)
        self.debug = self.list_zip
        

    #------------------------ _RUN_ANALYZE -------------------------------------
        
    @api.one
    def button_run_analyze(self):
        """
        SAVE ALL PDF AND TIFF
        
        """
        self.debug += "YOUPI"
        # list for checking if a file come twice
        check = []
        for attachment in self.data:
            if attachment.name not in check:
                check.append(attachment.name)
                # check for zip
                if check_file(attachment.name) == 2:
                    zip_ = zipfile.ZipFile(self.path+attachment.name,'r')
                    path_zip = self.path + os.path.splitext(str(attachment.name))[0]
                    if not os.path.exists(path_zip):
                        os.makedirs(path_zip)
                    for f in zip_.namelist():
                        """ ---------------------------------------------------
                        NEED TO CHECK THE DIRECTORY ---------------------------
                        """ # -------------------------------------------------
                        zip_.extract(f,path_zip)
                        a = self.analyze_attachment(path_zip+f)
                    shutil.rmtree(path_zip)
                    os.remove(self.path+attachment.name)
                elif check_file(attachment.name) == 1:
                    a = self.analyze_attachment(
                        self.path + attachment.name,
                        attachment.datas)
                else:
                    exceptions.Warning('Still a file in a non-accepted format')
            else:
                raise exceptions.Warning(_('Two files are the same'))
                return
        
    def analyze_attachment(self,file_,data=None):
        """
        Analyze attachment (PDF/TIFF) and save everything
        
        :param ir_attachment file_: current file to analyze
        """
        if data != None:
            f = open(file_,'w')
            f.write(base64.b64decode(data))
            f.close()

        tmp = zxing.BarCodeTool()
        if isTIFF(file_):
            try:
                code = tmp.decode(file_)
                partner,child = code.data.split('XX')
                sp_id = self.env['sponsorship_correspondence'].search(
                    [('partner_id.codega','=','partner'),
                     ('child_id.code','=','child')])[0].id
                
                if data == None:
                    f = open(file_,'r')
                    data = base64.b64encode(f.read())
                    f.close()
                partner = self.env['partner_id']
                self.env['sponsorship.correspondence'].create({
                    'letter_image': data,
                    'partner_id': partner,
                    'child_id': child,
                    'sponsorship_id': sp_id,
                })
                os.remove(file_)
                return code.data
            except:
                return 1
        else:
            """
            NEED TO CHECK DIRECTORY
            """
            exceptions.Warning('FORMAT NOT ACCEPTED')
            return 2
