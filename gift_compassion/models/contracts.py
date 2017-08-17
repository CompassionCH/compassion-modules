# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import datetime
import calendar

from odoo import api, models, fields, _
from odoo.exceptions import UserError

from odoo.addons.sponsorship_compassion.models.product import GIFT_CATEGORY


class SponsorshipContract(models.Model):
    _inherit = 'recurring.contract'

    no_birthday_invoice = fields.Boolean(
        help="The automatic birthday gift will not generate an invoice."
        "This means a birthday gift will always be sent to GMC "
        "even if we didn't register a payment."
    )
    number_gifts = fields.Integer(compute='_compute_nb_gifts')

    @api.multi
    def _compute_nb_gifts(self):
        gift_obj = self.env['sponsorship.gift']
        for contract in self:
            contract.number_gifts = gift_obj.search_count([
                ('sponsorship_id', '=', contract.id),
            ])

    @api.multi
    def invoice_paid(self, invoice):
        """ Prevent to reconcile invoices for fund-suspended projects
            or sponsorships older than 3 months. """
        for invl in invoice.invoice_line_ids:
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
        for invl in invoice.invoice_line_ids.filtered('gift_id'):
            gift = invl.gift_id
            if gift.gmc_gift_id and gift.state != 'Undeliverable':
                raise UserError(
                    _("You cannot delete the %s. It is already sent to GMC.")
                    % gift.name
                )
            # Remove the invoice line from the gift
            gift.write({'invoice_line_ids': [(3, invl.id)]})
            if not gift.invoice_line_ids:
                gift.unlink()
        super(SponsorshipContract, self).invoice_unpaid(invoice)

    @api.multi
    def open_gifts(self):
        return {
            'name': _('Sponsorship gifts'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sponsorship.gift',
            'domain': [('sponsorship_id', 'in', self.ids)],
            'context': self.env.context,
            'target': 'current',
        }

    def hold_gifts(self):
        for contract in self:
            today = datetime.date.today()
            first_day = today.replace(day=1)
            last_day = today.replace(day=calendar.monthrange(today.year,
                                                             today.month)[1])
            suspended_gifts = self.env['sponsorship.gift'].search([
                '&',
                ('child_id.project_id', '=', contract.project_id.id),
                ('create_date', '>=', str(first_day)),
                ('create_date', '<=', str(last_day)),
                '|',
                ('state', '=', 'open'),
                ('state', '=', 'In Progress'),
            ])
            suspended_gifts.action_suspended()

            related_move = suspended_gifts.mapped('payment_id')
            related_move.button_cancel()
            related_move.unlink()

        # Postpone open gifts.
        pending_gifts = self.env['sponsorship.gift'].search([
            ('sponsorship_id', 'in', self.ids),
            ('gmc_gift_id', '=', False)
        ])
        pending_gifts.action_verify()

    def reactivate_gifts(self):
        for contract in self:
            suspended_gifts = self.env['sponsorship.gift'].search([
                ('child_id.project_id', '=', contract.project_id.id),
                ('state', '=', 'suspended')
            ])
            suspended_gifts.action_in_progress()
            suspended_gifts.action_send()

        # Put again gifts in OK state.
        pending_gifts = self.env['sponsorship.gift'].search([
            ('sponsorship_id', 'in', self.ids),
            ('state', '=', 'verify')
        ])
        pending_gifts = pending_gifts.filtered(
            lambda g: g.is_eligible())
        pending_gifts.action_ok()
