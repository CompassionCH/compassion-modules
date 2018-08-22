# coding: utf-8
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    sponsorship_id = fields.Many2one('recurring.contract', 'Sponsorship')

    @api.multi
    def confirm_transaction(self):
        # Invoice is not yet linked at this stage so we link it.
        for transaction in self:
            if not transaction.invoice_id and 'SMS-1MONTH-' in \
                    transaction.reference:
                transaction.invoice_id = transaction.sponsorship_id\
                    .invoice_line_ids[-1].invoice_id
        return super(PaymentTransaction, self).confirm_transaction()

    def _get_auto_post_invoice(self):
        # The payment can only be posted if the sponsor was not created.
        if 'SMS-1MONTH-' in self.reference:
            return not self.sponsorship_id.sms_request_id.new_partner
        else:
            return super(PaymentTransaction, self)._get_auto_post_invoice()
