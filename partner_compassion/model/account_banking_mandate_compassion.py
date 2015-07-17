# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Steve Ferry
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, models


MANDATE_STATE = {'create': 'created',
                 'cancel': 'cancelled',
                 'validate': 'validated',
                 'back2draft': 'back to draft',
                 'delete': 'deleted'}


class Account_Banking_Mandate(models.Model):
    """ This class upgrade the partners.bank to match Compassion needs.
    """
    _inherit = 'account.banking.mandate'

    def _update_mandate_status_partner(self, action):
        """
        Post a message on the partner's message feed with the new state
        of the mandate
        """
        self.ensure_one()

        if action in MANDATE_STATE:
            self.partner_id.message_post(
                "For account: " + self.partner_bank_id.acc_number,
                "Mandate " + MANDATE_STATE[action], 'comment')

    @api.model
    def create(self, data):
        """Override function to notify creation in a message on partner feed
        """
        result = super(Account_Banking_Mandate, self).create(data)
        result._update_mandate_status_partner('create')

        return result

    @api.multi
    def validate(self):
        """
        Override function to notify validation in a message on partner feed
        """

        for mandate in self:
            mandate._update_mandate_status_partner('validate')

        super(Account_Banking_Mandate, self).validate()

        return True

    @api.multi
    def cancel(self):
        """
        Override function to notify cancellation in a message on partner feed
        """

        for mandate in self:
            mandate._update_mandate_status_partner('cancel')

        super(Account_Banking_Mandate, self).cancel()
        return True

    @api.multi
    def back2draft(self, cr, uid, ids, context=None):
        """
        Override function to notify cancellation in a message on partner feed
        """

        for mandate in self:
            mandate._update_mandate_status_partner('back2draft')

        super(Account_Banking_Mandate, self).back2draft()
        return True

    @api.multi
    def unlink(self, cr, uid, ids, context):
        """
        Override function to notify removal in a message on partner feed
        """

        for mandate in self:
            mandate._update_mandate_status_partner('delete')

        result = super(Account_Banking_Mandate, self).unlink()
        return result
