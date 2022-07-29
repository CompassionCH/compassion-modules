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
from zipfile import ZipFile

from odoo import models, api, fields, _


class DownloadLetters(models.TransientModel):
    """
    Utility to select multiple letters and download the attachments
    as a zip archive.
    """

    _name = "correspondence.download.wizard"
    _description = "Correspondence download wizard"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    fname = fields.Char(compute="_compute_filename")
    download_data = fields.Binary(readonly=True)

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    def _compute_filename(self):
        self.fname = fields.Date.context_today(self).strftime("%d-%m-%Y") \
            + _("_letters.zip")

    def _compute_data(self):
        """ Create the zip archive from the selected letters. """
        letters = (
            self.env[self.env.context["active_model"]]
            .browse(self.env.context["active_ids"])
            .with_context(bin_size=False)
        )
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, "w") as zip_data:
            for letter in letters:
                zip_data.writestr(
                    letter.file_name, base64.b64decode(letter.letter_image)
                )
        zip_buffer.seek(0)
        self.download_data = base64.b64encode(zip_buffer.read())

    def get_letters(self):
        self._compute_data()
        return {
            "type": "ir.actions.act_window",
            "res_id": self.id,
            "res_model": self._name,
            "view_mode": "form",
            "target": "new",
        }
