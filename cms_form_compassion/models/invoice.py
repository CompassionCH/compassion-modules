##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    @author: Robin Berguerand <robin.berguerand@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    auto_cancel_no_transaction = fields.Boolean(
        default=False, help='If true, cancel the invoice if the linked payment '
        'transaction is cancelled'
    )
