##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models


import logging

logger = logging.getLogger(__name__)


class ContractGroup(models.Model):
    _inherit = 'recurring.contract.group'

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _generate_birthday_gift(self, gift_wizard, contract):
        """
        Only generate invoice if no_birthday_invoice parameter is not set.
        Otherwise generate only the gift.
        :param gift_wizard: a generate_gift_wizard record
        :param contract:  the sponsorship
        :return: None
        """
        if contract.no_birthday_invoice:
            gift_obj = self.env['sponsorship.gift']
            gift_vals = gift_obj.get_gift_types(gift_wizard.product_id)
            gift_date = gift_wizard.compute_date_birthday_invoice(
                contract.child_id.birthdate,
                gift_wizard.invoice_date)
            # Search that a gift is not already pending
            existing_gifts = gift_obj.search([
                ('sponsorship_id', '=', contract.id),
                ('gift_date', 'like', gift_date[:4]),
                ('gift_type', '=', gift_vals['gift_type']),
                ('attribution', '=', gift_vals['attribution']),
                ('sponsorship_gift_type', '=', gift_vals.get(
                    'sponsorship_gift_type')),
            ])
            if not existing_gifts:
                # Create a gift record
                gift_vals['sponsorship_id'] = contract.id
                gift = gift_obj.create(gift_vals)
                gift.write({
                    'date_partner_paid': gift_date,
                    'gift_date': gift_date,
                    'amount': contract.birthday_invoice
                })
        else:
            super(ContractGroup, self)._generate_birthday_gift(gift_wizard,
                                                               contract)
