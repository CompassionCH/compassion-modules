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

import pdb
from tempfile import TemporaryFile
import zxing
from openerp import api, fields, models, _
from openerp.osv import osv
import sponsorship_correspondance

def check_file(name):
    """
    Check the name of a file.
    return 1 if it is a tiff or a pdf and 0 otherwise.
    
    :param str name: Name of the file to check
    :return: 1 if pdf or tiff, 0 otherwise
    :rtype: int
    """
    if (name[-4::].lower() in ['.pdf','.tif'] or  
        name[-5::].lower() == '.tiff'):
        return 1
    else:
        return 0


def isPDF(name):
    """
    Check the extension of the name
    """
    if name[-4::].lower() == '.pdf':
        return 1
    else:
        return 0

def isTIFF(name):
    """
    Check the extension of the name
    """
    if (name[-4::].lower() == '.tif' or
        name[-5::].lower() == '.tiff'):
        return 1
    else:
        return 0
    

def list2string(list_):
    """
    Transform a list to a string by separating the string in the list by ;
    """
    tmp = ''
    for i in list_:
        tmp += i + ';'
    return tmp

def addname(string, name):
    """
    Add name to string by separating them with ;
    """
    return string + name + ';'

def removename(string,name):
    """
    Remove name in string where string is a string separated with ;
    """
    i = string.find(name)
    if i == -1:
        return False
    else:
        return string[i:len(name)+1]



class ImportMail(models.Model):
    """
    Import mail
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
    list_zip = fields.Text("DEFAULT")
    list_zip = ""
    # list to check if attachment changed
    list_name = fields.Text()
    list_name = "DEFAULT"
    # dict that will be used to create correspondence
    #WRONG WRONG WRONG WRONG WRONG WRONG WRONG
    #WRONG WRONG WRONG WRONG WRONG WRONG WRONG
    #WRONG WRONG WRONG WRONG WRONG WRONG WRONG
    #WRONG WRONG WRONG WRONG WRONG WRONG WRONG
    #WRONG WRONG WRONG WRONG WRONG WRONG WRONG
    #WRONG WRONG WRONG WRONG WRONG WRONG WRONG
    bar = {'barcode' : [], 'attachment' : []}
    
    # link to _count_nber_files
    data = fields.Many2many('ir.attachment') 
    
    # removes old files in the directory
    if os.path.exists(path):
        onlyfiles = [ f for f in os.listdir(path)
                      if os.path.isfile(os.path.join(path,f)) ]
        # loop over files
        for f in onlyfiles:
            t = time.time()
            t -= os.path.getctime(path+f)
            # if file older than 1 week + 12h
            if t > 648000:
                os.remove(f)
    else:
        os.makedirs(path)
    
    #-------------------- _COUNT_NBER_FILES ------------------------------------
    
    @api.one
    @api.onchange("data")
    def _count_nber_files(self):
        """
        Counts the number of scans (if a zip is given, count the number
        inside it)
        """
        pdb.set_trace()
        tmp_list_name = self.mapped('data.name')
        if tmp_list_name != self.list_name.split(';'):
            self.list_name = list2string(tmp_list_name)
            # counter
            tmp = 0
            # loop over all the attachments
            for file_ in self.data:
                if ';' in file_:
                    raise osv.except_osv(_('Warning!'),
                                         _("Names should not contain ';'"))
                # pdf or tiff case
                #pdb.set_trace()
                if check_file(file_['name']):
                    tmp += 1
                # zip case
                elif file_['name'][-4::].lower() == '.zip':
                    # save the zip file
                    f = open(self.path+file_['name'],'w')
                    f.write(base64.b64decode(file_['datas']))
                    if file_['name'] not in self.list_zip:
                        self.list_zip = addname(self.list_zip,file_['name'])
                    f.close()
                    # catch ALL the exceptions that can be raised by class
                    # zipfile
                    try:
                        zip_ = zipfile.ZipFile(self.path+file_['name'],'r')
                    except zipfile.BadZipfile:
                        raise osv.except_osv(_('Error!'),
                                             _('Zip file corrupted (' + 
                                               file_['name'] + ')'))
                    except zipfile.LargeZipFile:
                        raise osv.except_osv(_('Error!'),
                                             _('Zip64 is not supported(' + 
                                               file_['name'] + ')'))
                    else:
                        list_file = zip_.namelist()
                        # loop over all files in zip
                        for tmp_file in list_file:
                            tmp += check_file(tmp_file)
            self.nber_file = tmp
            #self.debug = str(self.mapped('data.name'))
            # deletes zip removed from the data
            for f in self.list_zip.split(';'):
                if f not in self.mapped('data.name') and f!='':
                    if os.path.exists(self.path+f):
                        tmp = removename(self.list_zip,f)
                        if tmp != -1:
                            raise osv.except_osv(
                                _("Error!"),_("Problem for deleting a file"))
                        else:
                            self.list_zip = tmp
                        os.remove(self.path+f)
                        self.debug = self.list_zip
            self.debug = self.list_zip
            pdb.set_trace()
        
    #------------------------ _RUN_ANALYZE -------------------------------------
        
    @api.one
    def button_run_analyze(self):
        """
        SAVE ALL PDF AND TIFF
        
        """
        self.debug = "YOUPI"
        # list for checking if a file come twice
        check = []
        for file_ in self.data:
            if file_['name'] not in check:
                check.append(file_['name'])
                # check for zip
                if not check_file(file_['name']):
                    zip_ = zipfile.ZipFile(self.path+file_['name'],'r')
                    path_zip = path+file_['name'][-4::]
                    pdb.set_trace()
                    if not os.path.exists(path_zip):
                        os.makedirs(path_zip)
                    for f in zip_.namelist():
                        """ ---------------------------------------------------
                        NEED TO CHECK THE DIRECTORY ---------------------------
                        """ # -------------------------------------------------
                        zip_.extract(f,path_zip)
                        self.analyze_attachment(path_zip+f)
                    os.remove(path_zip)
                else:
                    self.analyze_attachment(
                        "/tmp/sbc_compassion/" + file_['name'],file_['datas'])
            else:
                raise osv.except_osv(_('Warning!'),
                                     _('Two files are the same'))
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

        tmp = zxing.BarCodeReader()
        if isPDF(file_):
            osv.except_osv('ERROR!','STILL IN DEV')
        if isTIFF(file_):
            code = tmp.decode(file_)
            if data == None:
                f = open(file_,'r')
                data = base64.b64encode(f.read())
            self.env['sponsorship.correspondence'].create({
                'letter_image': data,
                'sponsorship_id': 1,
            })
            print code.data.upper()
            print "ERROR NEED TO CORRECT SPONSORSHIP_ID"
        else:
            osv.except_osv('ERROR','FORMAT NOT ACCEPTED')
