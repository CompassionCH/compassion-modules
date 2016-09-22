# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, models

from openerp.addons.sponsorship_compassion.models.product import GIFT_CATEGORY


class SponsorshipContract(models.Model):
    _inherit = 'recurring.contract'

    @api.multi
    def invoice_paid(self, invoice):
        """ Prevent to reconcile invoices for fund-suspended projects
            or sponsorships older than 3 months. """
        for invl in invoice.invoice_line:
            if invl.product_id.categ_name == GIFT_CATEGORY and \
                    invl.contract_id.child_id:
                # Create the Sponsorship Gift
                self.env['sponsorship.gift'].create_from_invoice_line(invl)

        super(SponsorshipContract, self).invoice_paid(invoice)
