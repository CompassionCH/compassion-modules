##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Stephane Eicher <eicher31@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import models, api

_logger = logging.getLogger(__name__)

BOX_SEPARATOR = "#BOX#"
PAGE_SEPARATOR = "#PAGE#"


class FieldToJson(models.Model):
    _inherit = "compassion.field.to.json"

    @api.model
    def _format_correspondence_page(self, text):
        return text and text.split("\n" + BOX_SEPARATOR + "\n") or [""]
