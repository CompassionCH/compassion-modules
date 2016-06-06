# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import api, fields, models, _

from openerp.addons.message_center_compassion.mappings import base_mapping \
    as mapping


class ResPartner(models.Model):
    _inherit = 'res.partner'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    ref = fields.Char(
        required=True,
        default=lambda self: self.env['ir.sequence'].get('partner.ref'))
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
    mandatory_review = fields.Boolean(
        help='Indicates that we should review the letters of this sponsor '
             'before sending them to GMC.')
    other_contract_ids = fields.One2many(
        "recurring.contract", compute='_get_related_contracts',
        string='Other contracts')
    unrec_items = fields.Integer(compute='_set_count_items')
    receivable_items = fields.Integer(compute='_set_count_items')
    has_sponsorships = fields.Boolean(
        compute='_compute_has_sponsorships', store=True)
    send_original = fields.Boolean(
        help='Indicates that we request the original letters for this sponsor'
    )

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    @api.depends('category_id')
    def _compute_has_sponsorships(self):
        """
        A partner is sponsor if he is correspondent of at least one
        sponsorship.
        """
        for partner in self:
            partner.has_sponsorships = self.env[
                'recurring.contract'].search_count([
                    '|', ('partner_id', '=', partner.id),
                    ('correspondant_id', '=', partner.id),
                    ('type', 'like', 'S')
                ])

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
            partner.other_contract_ids = contract_obj.search(
                [('partner_id', '=', partner.id),
                 ('type', 'not in', ['S', 'SC'])],
                order='start_date desc').ids

    def _set_count_items(self):
        move_line_obj = self.env['account.move.line']
        for partner in self:
            partner.unrec_items = move_line_obj.search_count([
                ('partner_id', '=', partner.id),
                ('reconcile_id', '=', False),
                ('account_id.reconcile', '=', True)])
            partner.receivable_items = move_line_obj.search_count([
                ('partner_id', '=', partner.id),
                ('account_id.code', '=', '1050')])

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.multi
    def write(self, vals):
        notify_vals = ['firstname', 'lastname', 'name',
                       'mandatory_review', 'send_original']
        notify = reduce(lambda prev, val: prev or val in vals, notify_vals,
                        False)
        if notify and not self.env.context.get('no_upsert'):
            self.upsert_constituent()

        return super(ResPartner, self).write(vals)

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

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def process_commkit(self, commkit_data, model_action):
        """ Never used... nothing come from GMC about partner now! """
        object_mapping = mapping.new_onramp_mapping(self._name, self.env)
        object_data = object_mapping.get_vals_from_connect(commkit_data)
        # TODO update if partner exist.
        partner = self.create(object_data)
        return partner.id

    def convert_for_connect(self):
        """
        Method called when Create message is processed.
        """
        self.ensure_one()
        partner_mapping = mapping.new_onramp_mapping(self._name, self.env)
        return partner_mapping.get_connect_data(self)

    def get_connect_data(self, data):
        """ Enrich correspondence data with GMC data after CommKit Submission.
        """
        pass
        # self.ensure_one()
        # letter_mapping = mapping.new_onramp_mapping(self._name, self.env)
        # return self.write(letter_mapping.get_vals_from_connect(data))

    def upsert_constituent(self):
        """If partner has active contracts, UPSERT Constituent in GMC."""
        for partner in self:
            contract_count = self.env['recurring.contract'].search_count([
                ('correspondant_id', '=', partner.id),
                ('state', 'not in', ('terminated', 'cancelled'))])
            if contract_count:
                # UpsertConstituent Message if not one already pending
                message_obj = self.env['gmc.message.pool']
                action_id = self.env.ref(
                    'sponsorship_compassion.upsert_partner').id
                messages = message_obj.search([
                    ('partner_id', '=', partner.id),
                    ('state', '=', 'new'),
                    ('action_id', '=', action_id)])
                if not messages:
                    message_vals = {
                        'action_id': action_id,
                        'object_id': partner.id,
                        'partner_id': partner.id,
                    }
                    message_obj.create(message_vals)
