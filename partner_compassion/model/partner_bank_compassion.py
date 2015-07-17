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


class ResPartnerBank(models.Model):
    """ This class upgrade the partners.bank to match Compassion needs.
    """

    _inherit = 'res.partner.bank'

    @api.model
    def create(self, data):
        """Override function to notify creation in a message
        """
        result = super(ResPartnerBank, self).create(data)

        part = result.partner_id
        part.message_post("<b>Account number: </b>" + result.acc_number,
                          "New account created", 'comment')

        return result

    @api.multi
    def unlink(self):
        """Override function to notify delte in a message
        """
        for account in self:
            part = account.partner_id
            part.message_post("<b>Account number: </b>" + account.acc_number,
                              "Account deleted", 'comment')

        result = super(ResPartnerBank, self).unlink()
        return result
