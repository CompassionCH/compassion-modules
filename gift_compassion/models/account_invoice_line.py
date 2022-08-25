##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields


class InvoiceLine(models.Model):
    _inherit = "account.move.line"

    gift_id = fields.Many2one("sponsorship.gift", "GMC Gift", readonly=False)
