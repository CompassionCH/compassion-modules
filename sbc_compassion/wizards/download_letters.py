# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
from io import BytesIO
from odoo import models, api, fields, _
from zipfile import ZipFile


class DownloadLetters(models.TransientModel):
    """
    Utility to select multiple letters and download the attachments
    as a zip archive.
    """

    _name = 'correspondence.download.wizard'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    fname = fields.Char(default=lambda s: s.get_file_name())
    download_data = fields.Binary(
        readonly=True, default=lambda s: s.get_letters())

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.model
    def get_file_name(self):
        return fields.Date.context_today(self) + _('_letters.zip')

    @api.model
    def get_letters(self):
        """ Create the zip archive from the selected letters. """
        letters = self.env[self.env.context['active_model']].browse(
            self.env.context['active_ids'])
        letter_images = letters.mapped('letter_image')
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, 'w') as zip_data:
            for letter in letter_images:
                zip_data.writestr(letter.name, base64.b64decode(letter.datas))
        zip_buffer.seek(0)
        return base64.b64encode(zip_buffer.read())
