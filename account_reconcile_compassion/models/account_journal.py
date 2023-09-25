##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#             Nathan Fluckiger
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    payment_mode_id = fields.Many2one(
        "account.payment.mode", "Payment mode", readonly=False
    )
