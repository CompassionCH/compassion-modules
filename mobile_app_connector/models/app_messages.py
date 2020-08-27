##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields


class AppMessages(models.Model):
    _name = "mobile.app.messages"

    partner_id = fields.Many2one(
        "res.partner", "Partner", readonly=True, required=True
    )
    json_messages = fields.Char()
    last_refresh_date = fields.Date()
