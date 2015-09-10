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
from tempfile import TemporaryFile

from openerp import api, fields, models, _
from openerp.osv import osv

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



class ImportMail(models.Model):
    """
    Import mail
    """
    _name = "import.mail"
    _description = _("Import mail from a zip or a PDF/TIFF")
    
    # link to _count_nber_files
    data = fields.Many2many('ir.attachment') 
    nber_file = fields.Integer(_('Number of files: '),readonly=True,
                               compute="_count_nber_files")
    title = fields.Text(_("Import Mail"),readonly=True)
    debug = fields.Text("DEBUG",readonly=True)
    # path where the zipfile are store
    path = "/tmp/sbc_compassion/"
    # list zip in the many2many
    list_zip = []

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

#-------------------- _COUNT_NBER_FILES ----------------------------------------    

    @api.one
    @api.onchange("data")
    def _count_nber_files(self):
        """
        Counts the number of scans (if a zip is given, count the number
        inside it)
        """
        # counter
        tmp = 0
        # loop over all the attachments
        for file_ in self.data:
            # check if pdf or tiff
            tmp += check_file(file_['name'])
            # zip case
            if file_['name'][-4::].lower() == '.zip':
                # save the zip file
                f = open(self.path+file_['name'],'w')
                f.write(base64.b64decode(file_['datas']))
                self.list_zip.append(self.path+file_['name'])
                f.close()
                # catch all the exceptions that can be raised by zipfile
                try:
                    zip = zipfile.ZipFile(self.path+file_['name'],'r')
                except zipfile.BadZipfile:
                    raise osv.except_osv(_('Error!'),
                                         _('Zip file corrupted'))
                except zipfile.LargeZipFile:
                    raise osv.except_osv(_('Error!'),
                                         _('Zip64 is not supported'))
                else:
                    list_file = zip.namelist()
                    # loop over all files in zip
                    for tmp_file in list_file:
                        tmp += check_file(tmp_file)
        self.nber_file = tmp
        # deletes zip removed from the data
        self.debug = self.mapped('data.name')
        for f in self.list_zip:
            if f not in self.mapped('data.name'):
                if os.path.exists(f):
                    os.remove(f)
                self.list_zip.remove(f)
                

#------------------------ _RUN_ANALYZE -----------------------------------------                


    def _run_analyze(self):
        """
        CHECK DOUBLE ENTRY
        """
        #f = open(file_['name'],'w')
        #tmp = self.data[0]['datas']
        #f.write(base64.b64decode(str(tmp)))
        #f.close()
        return
