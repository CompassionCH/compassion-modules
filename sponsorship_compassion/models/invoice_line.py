##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester <csester@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class InvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    last_payment = fields.Date(related="invoice_id.last_payment", store=True)
