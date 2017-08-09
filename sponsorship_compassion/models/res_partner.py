# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from odoo import api, fields, models, _
from functools import reduce


class ResPartner(models.Model):
    _inherit = 'res.partner'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    global_id = fields.Char()
    contracts_fully_managed = fields.One2many(
        "recurring.contract", compute='_get_related_contracts',
        string='Fully managed sponsorships',
        order="state asc")
    contracts_paid = fields.One2many(
        "recurring.contract", compute='_get_related_contracts',
        string='Sponsorships as payer only')
    contracts_correspondant = fields.One2many(
        "recurring.contract", compute='_get_related_contracts',
        string='Sponsorships as correspondant only')
    sponsorship_ids = fields.One2many(
        "recurring.contract", compute='_get_related_contracts')
    mandatory_review = fields.Boolean(
        help='Indicates that we should review the letters of this sponsor '
             'before sending them to GMC.')
    other_contract_ids = fields.One2many(
        "recurring.contract", compute='_get_related_contracts',
        string='Other contracts')
    unrec_items = fields.Integer(compute='_set_count_items')
    receivable_items = fields.Integer(compute='_set_count_items')
    has_sponsorships = fields.Boolean(default=0)
    number_sponsorships = fields.Integer(default=0)
    send_original = fields.Boolean(
        help='Indicates that we request the original letters for this sponsor'
    )
    preferred_name = fields.Char()
    sponsored_child_ids = fields.One2many(
        'compassion.child', 'sponsor_id', 'Sponsored children')
    number_children = fields.Integer(compute='_compute_children')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    def _get_related_contracts(self):
        """ Returns the contracts of the sponsor of given type
        ('fully_managed', 'correspondant' or 'payer')
        """
        contract_obj = self.env['recurring.contract']
        for partner in self:
            partner.contracts_correspondant = contract_obj.search(
                [('correspondant_id', '=', partner.id),
                 ('type', 'in', ['S', 'SC']),
                 ('fully_managed', '=', False)],
                order='start_date desc').ids
            partner.contracts_paid = contract_obj.search(
                [('partner_id', '=', partner.id),
                 ('type', 'in', ['S', 'SC']),
                 ('fully_managed', '=', False)],
                order='start_date desc').ids
            partner.contracts_fully_managed = contract_obj.search(
                [('partner_id', '=', partner.id),
                 ('type', 'in', ['S', 'SC']),
                 ('fully_managed', '=', True)],
                order='start_date desc').ids
            partner.sponsorship_ids = partner.contracts_correspondant + \
                partner.contracts_paid + \
                partner.contracts_fully_managed
            partner.other_contract_ids = contract_obj.search(
                [('partner_id', '=', partner.id),
                 ('type', 'not in', ['S', 'SC'])],
                order='start_date desc').ids

    def _set_count_items(self):
        move_line_obj = self.env['account.move.line']
        for partner in self:
            partner.unrec_items = move_line_obj.search_count([
                ('partner_id', '=', partner.id),
                ('reconciled', '=', False),
                ('account_id.reconcile', '=', True)])
            partner.receivable_items = move_line_obj.search_count([
                ('partner_id', '=', partner.id),
                ('account_id.code', '=', '1050')])

    @api.multi
    def _compute_children(self):
        for partner in self:
            partner.number_children = len(partner.sponsored_child_ids)

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.multi
    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        notify_vals = ['firstname', 'lastname', 'name', 'preferred_name',
                       'mandatory_review', 'send_original']
        notify = reduce(lambda prev, val: prev or val in vals, notify_vals,
                        False)
        if notify and not self.env.context.get('no_upsert'):
            self.upsert_constituent()

        return res

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def show_lines(self):
        try:
            ir_model_data = self.env['ir.model.data']
            view_id = ir_model_data.get_object_reference(
                'sponsorship_compassion',
                'view_invoice_line_partner_tree')[1]
        except ValueError:
            view_id = False
        action = {
            'name': _('Related invoice lines'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice.line',
            'view_id': view_id,
            'views': [(view_id, 'tree'), (False, 'form')],
            'target': 'current',
            'context': self.with_context(
                search_default_partner_id=self.ids).env.context,
        }

        return action

    @api.multi
    def show_move_lines(self):
        try:
            ir_model_data = self.env['ir.model.data']
            move_line_id = ir_model_data.get_object_reference(
                'account',
                'view_move_line_tree')[1]
        except ValueError:
            move_line_id = False
        action = {
            'name': _('1050 move lines'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'account.move.line',
            'view_id': move_line_id,
            'views': [(move_line_id, 'tree')],
            'target': 'current',
            'context': self.with_context(
                search_default_partner_id=self.ids).env.context,
        }
        return action

    @api.multi
    def create_contract(self):
        self.ensure_one()
        context = self.with_context({
            'default_partner_id': self.id,
            'default_type': 'S',
            'type': 'S',
        }).env.context
        return {
            'type': 'ir.actions.act_window',
            'name': _('New Sponsorship'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'recurring.contract',
            'target': 'current',
            'context': context
        }

    @api.multi
    def unreconciled_transaction_items(self):
        return self.with_context(
            search_default_unreconciled=1).show_move_lines()

    @api.multi
    def receivable_transaction_items(self):
        account_ids = self.env['account.account'].search(
            [('code', '=', '1050')]).ids
        return self.with_context(
            search_default_account_id=account_ids[0]).show_move_lines()

    @api.multi
    def open_contracts(self):
        """ Used to bypass opening a contract in popup mode from
        res_partner view. """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contracts',
            'res_model': 'recurring.contract',
            'views': [[False, "tree"], [False, "form"]],
            'domain': ['|', ('correspondant_id', '=', self.id),
                       ('partner_id', '=', self.id)],
            'context': self.with_context({
                'default_type': 'S'}).env.context,
        }

    @api.multi
    def open_sponsored_children(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Children',
            'res_model': 'compassion.child',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'context': self.with_context(
                group_by=False,
                search_default_sponsor_id=self.id
            ).env.context,
        }

    @api.onchange('lastname', 'firstname')
    def onchange_preferred_name(self):
        self.preferred_name = self.firstname or self.name

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def upsert_constituent(self):
        """If partner has active contracts, UPSERT Constituent in GMC."""
        message_obj = self.env['gmc.message.pool'].with_context(
            async_mode=False)
        action_id = self.env.ref('sponsorship_compassion.upsert_partner').id
        for partner in self:
            contract_count = self.env['recurring.contract'].search_count([
                ('correspondant_id', '=', partner.id),
                ('state', 'not in', ('terminated', 'cancelled'))])
            if contract_count:
                # UpsertConstituent Message if not one already pending
                message_vals = {
                    'action_id': action_id,
                    'object_id': partner.id,
                    'partner_id': partner.id,
                }
                message_obj.create(message_vals)

    def update_church_sponsorships_number(self, inc):
        church = self.search([('members_ids', '=', self.id)])
        if inc and church:
            church.number_sponsorships += 1
        else:
            church.number_sponsorships -= 1
