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

from openerp import api, models, fields, _

from openerp.addons.sponsorship_compassion.models.product import GIFT_CATEGORY


class SponsorshipContract(models.Model):
    _inherit = 'recurring.contract'

    no_birthday_invoice = fields.Boolean(help=_(
        "The automatic birthday gift will not generate an invoice."
        "This means a birthday gift will always be sent to GMC "
        "even if we didn't register a payment."
    ))

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

    @api.multi
    def invoice_unpaid(self, invoice):
        """ Remove pending gifts or prevent unreconcile if gift are already
            sent.
        """
        invoice.invoice_line.mapped('gift_id').unlink()
        super(SponsorshipContract, self).invoice_unpaid(invoice)

    def hold_gifts(self):
        """ Postpone open gifts. """
        pending_gifts = self.mapped('invoice_line_ids.gift_id').filtered(
            lambda g: not g.gmc_gift_id)
        pending_gifts.action_verify()

    def reactivate_gifts(self):
        """ Put again gifts in OK state. """
        pending_gifts = self.mapped('invoice_line_ids.gift_id').filtered(
            lambda g: g.state == 'verify' and g.is_eligible())
        pending_gifts.action_ok()
