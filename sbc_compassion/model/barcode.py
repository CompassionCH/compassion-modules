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
This file reads a barcode from a PDF or a TIFF file
"""
import import_mail

class barcode:
    """
    class reading a barcode in a PDF/TIFF
    """

    def __init__(self,file_):
        self.file_ = file_
        

    def analyze(self):
        if import_mail.isPDF(self.file_):
            return self.analyzePDF()
        else:
            return self.analyzeTIFF()
        

    def analyzePDF(self):
        """
        Read a barcode in a PDF
        """
        #TODO

    def analyzeTIFF(self):
        """
        Read a barcode in a TIFF
        """
        #TODO
