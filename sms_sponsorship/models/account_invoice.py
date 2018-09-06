# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def _after_transaction_invoice_paid(self, transaction):
        """ Confirm step 2 and link invoice to transaction. """
        super(AccountInvoice, self)._after_transaction_invoice_paid(
            transaction)
        if transaction.sponsorship_id.sms_request_id:
            transaction.sponsorship_id.sms_request_id.complete_step2()
        return True
