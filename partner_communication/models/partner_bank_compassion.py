##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Steve Ferry
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, _
#TODO code retriven from v12 swiss -> when we migrate swiss into v14 that code should disappear


# pylint: disable=C8107
class ResPartnerBank(models.Model):
    """ This class upgrade the partners.bank to match Compassion needs.
    """

    _inherit = "res.partner.bank"

    def _account_notify_partner(self, account, action):
        """
        Post a message on the partner's message feed with the account infos
        """
        account.partner_id.message_post(
             body=_(f"Account {action}, account no: {account.acc_number or '' }"),
             subject=_(f"Account {action}"),
             type="comment",
        )

    def create(self, data):
        """Override function to notify creation in a message
        """
        result = super().create(data)
        if result.partner_id:
            self._account_notify_partner(result, 'created')

        return result

    def unlink(self):
        """Override function to notify delte in a message
        """
        for acc in self:
            self._account_notify_partner(acc, 'deleted')
        result = super().unlink()
        return result
