##############################################################################
#
#    Copyright (C) 2014-2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import random
import string
import functools

from odoo import api, fields, models, _
from odoo.exceptions import UserError


# For more flexibility we have split "res.partner" by functionality
# pylint: disable=R7980
class ResPartner(models.Model):
    _inherit = ['res.partner', 'compassion.mapped.model']
    _name = 'res.partner'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    global_id = fields.Char(copy=False)
    contracts_fully_managed = fields.One2many(
        "recurring.contract", compute='_compute_related_contracts',
        string='Fully managed sponsorships',
        order="state asc",
        groups="child_compassion.group_sponsorship")
    contracts_paid = fields.One2many(
        "recurring.contract", compute='_compute_related_contracts',
        string='Sponsorships as payer only',
        groups="child_compassion.group_sponsorship")
    contracts_correspondant = fields.One2many(
        "recurring.contract", compute='_compute_related_contracts',
        string='Sponsorships as correspondant only',
        groups="child_compassion.group_sponsorship")
    sponsorship_ids = fields.One2many(
        "recurring.contract", compute='_compute_related_contracts',
        groups="child_compassion.group_sponsorship")
    mandatory_review = fields.Boolean(
        help='Indicates that we should review the letters of this sponsor '
             'before sending them to GMC.',
        groups="child_compassion.group_sponsorship")
    other_contract_ids = fields.One2many(
        "recurring.contract", compute='_compute_related_contracts',
        string='Other contracts',
        groups="child_compassion.group_sponsorship")
    unrec_items = fields.Integer(compute='_compute_count_items',
                                 groups="child_compassion.group_sponsorship")
    receivable_items = fields.Integer(
        compute='_compute_count_items',
        groups="child_compassion.group_sponsorship")
    has_sponsorships = fields.Boolean(
        compute='_compute_has_sponsorships', store=True,
        groups="child_compassion.group_sponsorship")
    number_sponsorships = fields.Integer(copy=False)
    send_original = fields.Boolean(
        help='Indicates that we request the original letters for this sponsor',
        groups="child_compassion.group_sponsorship"
    )
    preferred_name = fields.Char()
    sponsored_child_ids = fields.One2many(
        'compassion.child', 'sponsor_id', 'Sponsored children',
        groups="child_compassion.group_sponsorship")
    number_children = fields.Integer(
        related='number_sponsorships',
        groups="child_compassion.group_sponsorship")
    privacy_statement_ids = fields.One2many(
        'privacy.statement.agreement', 'partner_id',
        groups='child_compassion.group_sponsorship', copy=False)
    member_ids = fields.One2many('res.partner', 'church_id', 'Members',
                                 domain=[('active', '=', True)])
    is_church = fields.Boolean(string="Is a Church",
                               compute='_compute_is_church', store=True)
    church_member_count = fields.Integer(compute='_compute_is_church',
                                         store=True)
    church_id = fields.Many2one('res.partner', 'Church',
                                domain=[('is_church', '=', True)])

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    def _compute_related_contracts(self):
        """ Returns the contracts of the sponsor of given type
        ('fully_managed', 'correspondent' or 'payer')
        """
        contract_obj = self.env['recurring.contract']
        for partner in self:
            partner.contracts_correspondant = contract_obj.search(
                [('correspondent_id', '=', partner.id),
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

    @api.multi
    def _compute_count_items(self):
        move_line_obj = self.env['account.move.line']
        for partner in self:
            partner.unrec_items = move_line_obj.search_count([
                ('partner_id', '=', partner.id),
                ('reconciled', '=', False),
                ('account_id.reconcile', '=', True),
                ('account_id.code', '=', '1050')
            ])
            partner.receivable_items = move_line_obj.search_count([
                ('partner_id', '=', partner.id),
                ('account_id.code', '=', '1050')])

    @api.multi
    def set_privacy_statement(self, origin):
        for partner in self:
            p_statement = self.env[
                'compassion.privacy.statement'].get_current()
            contract = self.env['privacy.statement.agreement'].search(
                [['partner_id', '=', partner.id],
                 ['privacy_statement_id', '=', p_statement.id]],
                order='agreement_date desc', limit=1)
            if contract:
                contract.agreement_date = fields.Date.today()
                contract.origin_signature = origin
            else:
                self.env['privacy.statement.agreement'].create(
                    {'partner_id': partner.id,
                     'agreement_date': fields.Date.today(),
                     'privacy_statement_id': p_statement.id,
                     'origin_signature': origin})

    @api.multi
    def update_number_sponsorships(self):
        for partner in self:
            partner.number_sponsorships = self.env['recurring.contract']\
                .search_count(partner._get_active_sponsorships_domain())
        return True

    @api.multi
    @api.depends('number_sponsorships')
    def _compute_has_sponsorships(self):
        for partner in self:
            partner.has_sponsorships = partner.number_sponsorships > 0

    @api.multi
    @api.depends('category_id', 'member_ids')
    def _compute_is_church(self):
        """ Tell if the given Partners are Church Partners
            (by looking at their categories). """

        # Retrieve all the categories and check if one is Church
        church_category = self.env['res.partner.category'].with_context(
            lang='en_US').search([('name', '=', 'Church')], limit=1)
        for record in self:
            is_church = False
            if church_category in record.category_id:
                is_church = True

            record.church_member_count = len(record.member_ids)
            record.is_church = is_church

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        # Put a preferred name
        partner = super().create(vals)
        if not partner.preferred_name:
            partner.preferred_name = \
                partner.firstname or partner.lastname or partner.name
        return partner

    @api.multi
    def write(self, vals):
        if 'firstname' in vals and 'preferred_name' not in vals:
            vals['preferred_name'] = vals['firstname']
        res = super().write(vals)
        notify_vals = ['firstname', 'lastname', 'name', 'preferred_name',
                       'mandatory_review', 'send_original', 'title']
        notify = functools.reduce(
            lambda prev, val: prev or val in vals, notify_vals, False)
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
                'recurring.contract',
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
        tree_view_id = self.env.ref('account.view_move_line_tree').id
        form_view_id = self.env.ref('account.view_move_line_form').id
        action = {
            'name': _('1050 move lines'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'account.move.line',
            'view_id': tree_view_id,
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
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
            search_default_unreconciled=1).receivable_transaction_items()

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
            'views': [[False, "tree"], [False, "form"], [False, "timeline"]],
            'domain': self._get_active_sponsorships_domain(),
        }

    @api.multi
    def open_sponsored_children(self):
        self.ensure_one()
        children = self.env['recurring.contract'].search(
            self._get_active_sponsorships_domain()).mapped('child_id')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Children',
            'res_model': 'compassion.child',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', children.ids)],
        }

    @api.onchange('lastname', 'firstname')
    def onchange_preferred_name(self):
        self.preferred_name = self.firstname or self.name

    @api.multi
    def forget_me(self):
        """ Anonymize partner and delete sensitive data.
        This will call the GDPR Data Protection Request on Connect,
        Remove all letters and communication history, and attachments.
        """
        if self.global_id:
            action = self.env.ref('sponsorship_compassion.anonymize_partner')
            message = self.env['gmc.message'].with_context(
                async_mode=False).create({
                    'action_id': action.id,
                    'object_id': self.id,
                    'partner_id': self.id
                })
            if message.state == 'failure':
                answer = message.get_answer_dict()
                raise UserError(
                    answer and answer.get('DataProtection Error',
                                          message.failure_reason)
                    or message.failure_reason
                )

        def _random_str():
            return ''.join([
                random.choice(string.ascii_letters) for n in range(8)])

        # Anonymize and delete partner data
        self.with_context(no_upsert=True).write({
            'name': _random_str(),
            'firstname': False,
            'preferred_name': False,
            'parent_id': False,
            'image': False,
            'phone': False,
            'mobile': False,
            'email': False,
            'street': _random_str(),
            'street2': _random_str(),
            'website': False,
            'birthdate': False,
            'function': False,
            'category_id': False,
            'comment': False,
            'active': False
        })
        # Delete message and mail history
        self.message_ids.unlink()
        self.env['mail.mail'].search([
            ('recipient_ids', '=', self.id)
        ]).unlink()
        self.env['ir.attachment'].search([
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.id)
        ]).unlink()
        self.bank_ids.unlink()
        self.privacy_statement_ids.unlink()
        self.user_ids.sudo().unlink()
        self.env['gmc.message'].search([
            ('partner_id', '=', self.id)]).write({
                'res_name': self.name
            })
        return True

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def upsert_constituent(self):
        """If partner has active contracts, UPSERT Constituent in GMC."""
        message_obj = self.env['gmc.message'].with_context(
            async_mode=False)
        messages = message_obj
        action_id = self.env.ref('sponsorship_compassion.upsert_partner').id
        for partner in self:
            contract_count = self.env['recurring.contract'].search_count([
                ('correspondent_id', '=', partner.id),
                ('state', 'not in', ('terminated', 'cancelled'))])
            if contract_count:
                # UpsertConstituent Message if not one already pending
                message_vals = {
                    'action_id': action_id,
                    'object_id': partner.id,
                    'partner_id': partner.id,
                }
                messages += message_obj.create(message_vals)
        return messages

    def _get_active_sponsorships_domain(self):
        """
        Get a search domain to fetch active sponsorships of the given
        partners.
        :return: domain search filter for recurring.contract object
        """
        return [
            '|',
            ('partner_id', 'in', self.ids),
            ('correspondent_id', 'in', self.ids),
            ('activation_date', '!=', False),
            ('state', 'not in', ['cancelled', 'terminated']),
            ('child_id', '!=', False)
        ]

    @api.model
    def json_to_data(self, json, mapping_name=None):

        if 'GPID' in json:
            json['GPID'] = json['GPID'][3:]

        connect_data = super().json_to_data(json, mapping_name)

        if not connect_data.get('GlobalID') and 'GlobalID' in connect_data:
            del connect_data['GlobalID']

        return connect_data
