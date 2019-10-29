# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields, _


class ContractOrigin(models.Model):
    """ Add event to origin of a contract """
    _inherit = 'recurring.contract.origin'

    event_id = fields.Many2one('crm.event.compassion', 'Event')

    @api.depends('type')
    def _compute_name(self):
        for origin in self:
            if origin.type == 'event':
                origin.name = origin.event_id.full_name
            else:
                super(ContractOrigin, origin)._compute_name()

    @api.multi
    def write(self, vals):
        """ Propagate ambassador into contracts and invoice lines. """
        if 'partner_id' in vals:
            for origin in self:
                old_ambassador_id = origin.partner_id.id
                sponsorships = self.env['recurring.contract'].search([
                    ('origin_id', '=', origin.id),
                    ('user_id', '=', old_ambassador_id)
                ])
                sponsorships.write({'user_id': vals['partner_id']})
                invoice_lines = self.env['account.invoice.line'].search([
                    ('contract_id', 'in', sponsorships.ids)]
                )
                invoice_lines.write({'user_id': vals['partner_id']})
        return super(ContractOrigin, self).write(vals)

    def _find_same_origin(self, vals):
        return self.search([
            ('type', '=', vals.get('type')),
            ('partner_id', '=', vals.get('partner_id')),
            '|', ('analytic_id', '=', vals.get('analytic_id')),
            ('event_id', '=', vals.get('event_id')),
            ('country_id', '=', vals.get('country_id')),
            ('other_name', '=', vals.get('other_name')),
        ], limit=1)


class Contracts(models.Model):
    """ Adds the Salesperson to the contract. """

    _inherit = 'recurring.contract'

    user_id = fields.Many2one('res.partner', 'Ambassador')

    @api.onchange('origin_id')
    def on_change_origin(self):
        origin = self.origin_id
        if origin:
            self.user_id = self._get_user_from_origin(origin)

    @api.onchange('child_id')
    def onchange_child_id(self):
        hold = self.hold_id
        origin = hold.origin_id
        if origin:
            self.origin_id = origin
        if hold.channel and hold.channel == 'web':
            self.channel = 'internet'
        if hold.ambassador:
            self.user_id = hold.ambassador
        self.campaign_id = hold.campaign_id
        if hold.comments:
            return {
                'warning': {'title': _('The child has some comments'),
                            'message': hold.comments}
            }

    def _get_user_from_origin(self, origin):
        user_id = False
        if origin.partner_id:
            user_id = origin.partner_id.id
        elif origin.event_id and origin.event_id.user_id:
            user_id = origin.event_id.user_id.partner_id.id
        elif origin.analytic_id and origin.analytic_id.partner_id:
            user_id = origin.analytic_id.partner_id.id
        return user_id


class ContractGroup(models.Model):
    """ Push salesperson to invoice on invoice generation """
    _inherit = 'recurring.contract.group'

    def _setup_inv_line_data(self, contract_line, invoice_id):
        invl_data = super(ContractGroup, self)._setup_inv_line_data(
            contract_line, invoice_id)
        if contract_line.contract_id.user_id:
            invl_data['user_id'] = contract_line.contract_id.user_id.id
        return invl_data
