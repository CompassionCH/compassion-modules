##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.addons.child_compassion.models.compassion_hold import HoldType
from odoo.addons.queue_job.job import job, related_action

from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import os

from .product import GIFT_CATEGORY, SPONSORSHIP_CATEGORY
import logging
logger = logging.getLogger(__name__)
THIS_DIR = os.path.dirname(__file__)


class SponsorshipContract(models.Model):
    _inherit = 'recurring.contract'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    correspondent_id = fields.Many2one(
        'res.partner', string='Correspondent', track_visibility='onchange',
        oldname='correspondant_id'
    )
    partner_codega = fields.Char(
        'Partner ref', related='correspondent_id.ref', readonly=True)
    fully_managed = fields.Boolean(
        compute='_compute_fully_managed', store=True)
    birthday_invoice = fields.Float(
        "Annual birthday gift",
        help="Set the amount to enable automatic invoice creation each year "
        "for a birthday gift. The invoice is set two months before "
        "child's birthday.", track_visibility='onchange')
    reading_language = fields.Many2one(
        'res.lang.compassion', 'Preferred language', required=False,
        track_visiblity='onchange')
    transfer_partner_id = fields.Many2one(
        'compassion.global.partner', 'Transferred to')
    global_id = fields.Char(help='Connect global ID', readonly=True,
                            copy=False, track_visibility='onchange')
    hold_expiration_date = fields.Datetime(
        help='Used for setting a hold after sponsorship cancellation')
    send_gifts_to = fields.Selection([
        ('partner_id', 'Payer'),
        ('correspondent_id', 'Correspondent')
    ], default='correspondent_id')
    gift_partner_id = fields.Many2one('res.partner',
                                      compute='_compute_gift_partner')
    contract_line_ids = fields.One2many(
        default=lambda self: self._get_standard_lines()
    )
    preferred_name = fields.Char(related='child_id.preferred_name')
    suspended_amount = fields.Float(compute='_compute_suspended_amount')

    _sql_constraints = [
        ('unique_global_id', 'unique(global_id)', 'You cannot have same '
                                                  'global ids for contracts')
    ]
    #

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def _get_standard_lines(self):
        if 'S' in self.env.context.get('default_type', 'O'):
            return self._get_sponsorship_standard_lines(False)
        return []

    @api.onchange('type')
    def _create_empty_lines_for_correspondence(self):
        self.contract_line_ids = self._get_sponsorship_standard_lines(
            self.type == 'SC')

    @api.model
    def _get_sponsorship_standard_lines(self, correspondence):
        """ Select Sponsorship and General Fund by default """
        res = []
        sponsorship_product = self.env.ref(
            'sponsorship_compassion.'
            'product_template_sponsorship').product_variant_id
        gen_product = self.env.ref(
            'sponsorship_compassion.'
            'product_template_fund_gen').product_variant_id
        sponsorship_vals = {
            'product_id': sponsorship_product.id,
            'quantity': 0 if correspondence else 1,
            'amount': 0 if correspondence else sponsorship_product.list_price,
            'subtotal': 0 if correspondence else sponsorship_product.list_price
        }
        gen_vals = {
            'product_id': gen_product.id,
            'quantity': 0 if correspondence else 1,
            'amount': 0 if correspondence else gen_product.list_price,
            'subtotal': 0 if correspondence else gen_product.list_price
        }
        res.append([0, 6, sponsorship_vals])
        res.append([0, 6, gen_vals])
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        """ Display only contract type needed in view.
        """
        res = super().fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)

        if view_type == 'form' and 'type' in res['fields']:
            s_type = self._context.get('default_type', 'O')
            if 'S' in s_type:
                # Remove non sponsorship types
                res['fields']['type']['selection'].pop(0)
                res['fields']['type']['selection'].pop(0)
            else:
                # Remove type Sponsorships so that we cannot change to it.
                res['fields']['type']['selection'].pop(2)
                res['fields']['type']['selection'].pop(2)

        return res

    @api.multi
    @api.depends('partner_id', 'correspondent_id')
    def _compute_fully_managed(self):
        """Tells if the correspondent and the payer is the same person."""
        for contract in self:
            contract.fully_managed = (contract.partner_id ==
                                      contract.correspondent_id)

    @api.model
    def _get_type(self):
        res = super()._get_type()
        res.extend([
            ('G', _('Child Gift')),
            ('S', _('Sponsorship')),
            ('SC', _('Correspondence'))])
        return res

    @api.multi
    def _compute_last_paid_invoice(self):
        """ Override to exclude gift invoices. """
        for contract in self:
            contract.last_paid_invoice_date = max(
                contract.invoice_line_ids.with_context(lang='en_US').filtered(
                    lambda l: l.state == 'paid' and
                    l.product_id.categ_name != GIFT_CATEGORY).mapped(
                        'invoice_id.date_invoice') or [False])

    @api.multi
    def _compute_invoices(self):
        gift_contracts = self.filtered(lambda c: c.type == 'G')
        for contract in gift_contracts:
            invoices = contract.mapped(
                'contract_line_ids.sponsorship_id.invoice_line_ids.invoice_id')
            gift_invoices = invoices.filtered(
                lambda i: i.invoice_type == 'gift' and i.state not in
                ('cancel', 'draft'))
            contract.nb_invoices = len(gift_invoices)
        super(SponsorshipContract, self - gift_contracts)._compute_invoices()

    @api.multi
    def _compute_gift_partner(self):
        for contract in self:
            contract.gift_partner_id = getattr(
                contract, contract.send_gifts_to, contract.correspondent_id)

    @api.multi
    def _compute_suspended_amount(self):
        """ Suspended amount is all amount donated to suspension product
        and amount not reconciled. """
        suspend_config = int(self.env['ir.config_parameter'].get_param(
            'sponsorship_compassion.suspend_product_id', 0))
        suspend_product = self.env['product.product'].browse(
            suspend_config).exists()
        for contract in self.filtered('child_id'):
            amount = 0
            if suspend_product:
                amount += sum(self.env['account.invoice.line'].search([
                    ('contract_id', '=', contract.id),
                    ('state', '=', 'paid'),
                    ('product_id', '=', suspend_product.id)
                ]).mapped('price_subtotal') or [0])
            amount += contract.partner_id.debit
            contract.suspended_amount = amount

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################

    @api.model
    def create(self, vals):
        """ Perform various checks on contract creations
        """
        # Force the commitment_number
        partner_ids = []
        partner_id = vals.get('partner_id')
        if partner_id:
            partner_ids.append(partner_id)
        correspondent_id = vals.get('correspondent_id')
        if correspondent_id and correspondent_id != partner_id:
            partner_ids.append(correspondent_id)
        if partner_ids:
            other_nums = self.search([
                '|', ('partner_id', 'in', partner_ids),
                ('correspondent_id', 'in', partner_ids),
                ('state', 'not in', ['cancelled', 'terminated'])
            ]).mapped('commitment_number')
            vals['commitment_number'] = max(other_nums or [0]) + 1
        else:
            vals['commitment_number'] = 1

        child = self.env['compassion.child'].browse(vals.get('child_id'))
        sponsor_id = vals.get('correspondent_id', vals.get('partner_id'))
        if 'S' in vals.get('type', '') and child and sponsor_id:
            child.write({
                'sponsor_id': sponsor_id
            })

        # Generates commitment number for contracts BVRs
        if 'commitment_number' not in vals:
            partner_id = vals.get('partner_id')
            correspondent_id = vals.get('correspondent_id', partner_id)
            if partner_id:
                other_nums = self.search([
                    '|', '|', '|', ('partner_id', '=', partner_id),
                    ('partner_id', '=', correspondent_id),
                    ('correspondent_id', '=', partner_id),
                    ('correspondent_id', '=', correspondent_id)
                ]).mapped('commitment_number')

                vals['commitment_number'] = max(other_nums or [-1]) + 1
            else:
                vals['commitment_number'] = 1

        return super().create(vals)

    @api.multi
    def write(self, vals):
        """ Perform various checks on contract modification """
        if 'child_id' in vals:
            self._link_unlink_child_to_sponsor(vals)

        if 'partner_id' in vals:
            old_partners = self.mapped('partner_id')

        updated_correspondents = self.env[self._name]
        if 'correspondent_id' in vals:
            old_correspondents = self.mapped('correspondent_id')
            updated_correspondents = self._on_change_correspondant(
                vals['correspondent_id'])
            self.mapped('child_id').write({
                'sponsor_id': vals['correspondent_id']
                })

        super().write(vals)

        try:
            with self.env.cr.savepoint():
                if updated_correspondents:
                    updated_correspondents._on_correspondant_changed()
        except:
            logger.error(
                "Error while changing correspondant at GMC. "
                "The sponsorship is no longer active at GMC side. "
                "Please activate it again manually.", exc_info=True
                )

        if 'reading_language' in vals:
            (self - updated_correspondents)._on_language_changed()

        if 'partner_id' in vals:
            # Move invoices to new partner
            invoices = self.invoice_line_ids.mapped('invoice_id').filtered(
                lambda i: i.state in ('open', 'draft'))
            invoices.action_invoice_cancel()
            invoices.action_invoice_draft()
            invoices.write({'partner_id': vals['partner_id']})
            invoices.action_invoice_open()
            # Update number of sponsorships
            self.mapped('partner_id').update_number_sponsorships()
            old_partners.update_number_sponsorships()

        if 'correspondent_id' in vals:
            self.mapped('correspondent_id').update_number_sponsorships()
            old_correspondents.update_number_sponsorships()

        return True

    @api.multi
    def unlink(self):
        for contract in self:
            # We can only delete draft sponsorships.
            if 'S' in contract.type and contract.state != 'draft':
                raise UserError(
                    _('You cannot delete a validated sponsorship.'))
            # Remove sponsor of child
            if 'S' in contract.type and contract.child_id:
                child_sponsor_id = contract.child_id.sponsor_id and \
                    contract.child_id.sponsor_id.id
                if child_sponsor_id == contract.correspondent_id.id:
                    contract.child_id.signal_workflow('release')
        return super().unlink()

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def _on_invoice_line_removal(self, invl_rm_data):
        pass

    @api.multi
    def suspend_contract(self):
        """
        If ir.config.parameter is set : change sponsorship invoices with
        a fund donation set in the config.
        Otherwise, Cancel the number of invoices specified starting
        from a given date. This is useful to suspend a contract for a given
        period."""
        ids = str(self.ids)
        logger.info(f"suspension of contracts {ids} called")
        date_start = datetime.today().strftime(DF)

        config_obj = self.env['ir.config_parameter']
        suspend_config = config_obj.get_param(
            'sponsorship_compassion.suspend_product_id')
        # Cancel invoices in the period of suspension
        self._clean_invoices(
            date_start, keep_lines=_('Center suspended'))

        for contract in self:
            # Add a note in the contract and in the partner.
            project_code = contract.project_id.fcp_id
            contract.message_post(
                f"The project {project_code} was suspended and funds are retained."
                "<br/>Invoices due in the suspension period "
                "are automatically cancelled.",
                f"Project Suspended",
                f"comment")
            contract.partner_id.message_post(
                f"The project {project_code} was suspended and funds are retained for child {contract.child_code}. <b>"
                    "<br/>Invoices due in the suspension period "
                    "are automatically cancelled.",
                f"Project Suspended",
                f"comment")

        # Change invoices if config tells to do so.
        if suspend_config:
            product_id = int(suspend_config)
            self._suspend_change_invoices(date_start,
                                          product_id)

        return True

    @api.multi
    def _suspend_change_invoices(self, since_date, product_id):
        """ Change cancelled sponsorship invoices and put them for given
        product. Re-open invoices. """
        cancel_inv_lines = self.env['account.invoice.line'].with_context(
            lang='en_US').search([
                ('contract_id', 'in', self.ids),
                ('state', '=', 'cancel'),
                ('product_id.categ_name', '=', SPONSORSHIP_CATEGORY),
                ('due_date', '>=', since_date)])
        invoices = cancel_inv_lines.mapped('invoice_id')
        invoices.action_invoice_draft()
        invoices.env.clear()
        vals = self.get_suspend_invl_data(product_id)
        cancel_inv_lines.write(vals)
        invoices.action_invoice_open()

    @api.multi
    def get_suspend_invl_data(self, product_id):
        """ Returns invoice_line data for a given product when center
        is suspended. """

        product = self.env['product.product'].browse(product_id)
        vals = {
            'product_id': product_id,
            'account_id': product.property_account_income_id.id,
            'name': 'Replacement of sponsorship (fund-suspended)'}
        rec = self.env['account.analytic.default'].account_get(product.id)
        if rec and rec.analytic_id:
            vals['account_analytic_id'] = rec.analytic_id.id

        return vals

    @api.multi
    def reactivate_contract(self):
        """ When project is reactivated, we re-open cancelled invoices,
        or we change open invoices if fund is set to replace sponsorship
        product. We also change attribution of invoices paid in advance.
        """
        date_start = datetime.today().strftime(DF)
        config_obj = self.env['ir.config_parameter']
        suspend_config = config_obj.get_param(
            'sponsorship_compassion.suspend_product_id')
        invl_obj = self.env['account.invoice.line']
        sponsorship_product = self.env['product.product'].with_context(
            lang='en_US').search([('name', '=', 'Sponsorship')])
        if suspend_config:
            # Revert future invoices with sponsorship product
            susp_product_id = int(suspend_config)
            invl_lines = invl_obj.search([
                ('contract_id', 'in', self.ids),
                ('product_id', '=', susp_product_id),
                ('state', 'in', ['open', 'paid']),
                ('due_date', '>=', date_start)])
            invl_data = {
                'product_id': sponsorship_product.id,
                'account_id':
                sponsorship_product.property_account_income_id.id,
                'name': sponsorship_product.name
            }
            rec = self.env['account.analytic.default'].account_get(
                sponsorship_product.id)
            if rec and rec.analytic_id:
                invl_data['account_analytic_id'] = rec.analytic_id.id
            invl_lines.write(invl_data)

            invoices = invl_lines.mapped('invoice_id')
            contracts = invl_lines.mapped('contract_id')
            reconciles = invoices.filtered(
                lambda inv: inv.state == 'paid').mapped(
                'payment_move_line_ids.full_reconcile_id')

            # Unreconcile paid invoices
            reconciles.mapped('reconciled_line_ids').remove_move_reconcile()
            # Cancel and confirm again invoices to update move lines
            invoices.action_invoice_cancel()
            invoices.action_invoice_draft()
            invoices.env.clear()
            invoices.action_invoice_open()
        else:
            # Open again cancelled invoices
            inv_lines = invl_obj.search([
                ('contract_id', 'in', self.ids),
                ('product_id', '=', sponsorship_product.id),
                ('state', '=', 'cancel'),
                ('due_date', '>=', date_start)])
            contracts = inv_lines.mapped('contract_id')
            to_open = inv_lines.mapped('invoice_id').filtered(
                lambda inv: inv.state == 'cancel')
            to_open.action_invoice_draft()
            to_open.env.clear()
            for i in to_open:
                i.action_invoice_open()

        # Log a note in the contracts
        for contract in contracts:
            contract.message_post(
                _("The project was reactivated."
                    "<br/>Invoices due in the suspension period "
                    "are automatically reverted."),
                _("Project Reactivated"), _('comment'))

    def commitment_sent(self, vals):
        """ Called when GMC received the commitment. """
        self.ensure_one()
        # We don't need to write back partner and child
        del vals['child_id']
        del vals['correspondent_id']
        self.write(vals)
        # Remove the hold on the child.
        if self.child_id.hold_id:
            self.child_id.hold_id.state = 'expired'
            self.child_id.hold_id = False
        return True

    def cancel_sent(self, vals):
        """ Called when GMC received the commitment cancel request. """
        self.ensure_one()
        if self.hold_expiration_date:
            hold_expiration = fields.Datetime.from_string(
                self.hold_expiration_date)
            if 'hold_id' in vals and hold_expiration >= datetime.now():
                child = self.child_id
                hold_vals = {
                    'hold_id': vals['hold_id'],
                    'child_id': child.id,
                    'type': HoldType.SPONSOR_CANCEL_HOLD.value,
                    'channel': 'sponsor_cancel',
                    'expiration_date': self.hold_expiration_date,
                    'primary_owner': self.write_uid.id,
                    'state': 'active',
                }
                hold = self.env['compassion.hold'].create(hold_vals)
                child.write({'hold_id': hold.id})
        return True

    @api.multi
    def get_inv_lines_data(self):
        """ Contract gifts relate their invoice lines to sponsorship,
            Correspondence sponsorships don't create invoice lines.
            Add analytic account to invoice_lines.
        """
        contracts = self.filtered(lambda c: c.total_amount != 0)
        suspend_config = int(self.env['ir.config_parameter'].get_param(
            'sponsorship_compassion.suspend_product_id', 0))
        res = list()
        for contract in contracts:
            invl_datas = super().get_inv_lines_data()

            # If project is suspended, either skip invoice or replace product
            if contract.type in ['S', 'SC'] and \
                    contract.project_id.hold_cdsp_funds:
                if not suspend_config:
                    continue
                for invl_data in invl_datas:
                    current_product = self.env['product.product'].with_context(
                        lang='en_US').browse(invl_data['product_id'])
                    if current_product.categ_name == SPONSORSHIP_CATEGORY:
                        invl_data.update(self.get_suspend_invl_data(
                            suspend_config))

            if contract.type == 'G':
                for i in range(0, len(invl_datas)):
                    sponsorship = contract.contract_line_ids[
                        i].sponsorship_id
                    gen_states = sponsorship.group_id._get_gen_states()
                    if sponsorship.state in gen_states and not \
                            sponsorship.project_id.hold_gifts:
                        invl_datas[i]['contract_id'] = sponsorship.id
                    else:
                        logger.error(
                            f"No active sponsorship found for child {sponsorship.child_code}. "
                            f"The gift contract with id {contract.id} is not valid."
                            )
                        continue

            # Find the analytic account
            for invl_data in invl_datas:
                contract = self.env['recurring.contract'].browse(
                    invl_data['contract_id'])
                product_id = invl_data['product_id']
                partner_id = contract.partner_id.id
                analytic = contract.origin_id.analytic_id
                if not analytic:
                    a_default = self.env[
                        'account.analytic.default'].account_get(
                            product_id, partner_id, date=fields.Date.today())
                    analytic = a_default and a_default.analytic_id
                if analytic:
                    invl_data.update({
                        'account_analytic_id': analytic.id})

            # Append the invoice lines.
            res.extend(invl_datas)

        return res

    @api.multi
    @job(default_channel='root.sponsorship_compassion')
    @related_action(action='related_action_contract')
    def put_child_on_no_money_hold(self):
        """Convert child to No Money Hold"""
        self.ensure_one()
        return self.child_id.hold_id.write({
            'expiration_date': self.env[
                'compassion.hold'].get_default_hold_expiration(
                HoldType.NO_MONEY_HOLD),
            'type': HoldType.NO_MONEY_HOLD.value,
        })

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.onchange('partner_id', 'correspondent_id')
    def on_change_partner_correspondent_id(self):
        """ On partner change, we set the new commitment number
        (for gift identification). """
        partners = self.partner_id + self.correspondent_id
        contracts = self.search([
            '|',
            ('partner_id', 'in', partners.ids),
            ('correspondent_id', 'in', partners.ids),
            ('state', 'not in', ['terminated', 'cancelled']),
        ])
        self.commitment_number = max(
            contracts.mapped('commitment_number') or [0]) + 1
        if self.partner_id and not self.correspondent_id:
            self.correspondent_id = self.partner_id

    @api.multi
    def open_invoices(self):
        res = super().open_invoices()
        if self.type == 'G':
            # Include gifts of related sponsorship for gift contracts
            sponsorship_invoices = self.mapped(
                'contract_line_ids.sponsorship_id.invoice_line_ids.invoice_id')
            gift_invoices = sponsorship_invoices.filtered(
                lambda i: i.invoice_type == 'gift')
            res['domain'] = [('id', 'in', gift_invoices.ids)]
        return res

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    @api.multi
    def contract_active(self):
        """ Hook for doing something when contract is activated.
        Update child to mark it has been sponsored,
        and activate gift contracts.
        Send messages to GMC.
        """
        for contract in self.filtered(lambda c: 'S' in c.type):
            # UpsertConstituent Message
            partner = contract.correspondent_id
            partner.upsert_constituent()

            message_obj = self.env['gmc.message']
            action_id = self.env.ref(
                'sponsorship_compassion.create_sponsorship').id

            message_vals = {
                'partner_id': contract.correspondent_id.id,
                'child_id': contract.child_id.id,
                'action_id': action_id,
                'object_id': contract.id
            }
            message_obj.create(message_vals)

        super().contract_active()
        con_line_obj = self.env['recurring.contract.line']
        for contract in self.filtered(lambda c: 'S' in c.type):
            gift_contract_lines = con_line_obj.search([
                ('sponsorship_id', '=', contract.id)])
            gift_contract_lines.mapped('contract_id').contract_active()

        partners = self.mapped('partner_id') | self.mapped('correspondent_id')
        partners.update_number_sponsorships()
        return True

    @api.multi
    def contract_cancelled(self):
        res = super().contract_cancelled()
        self.filtered(lambda c: c.type == 'S')._on_sponsorship_finished()
        return res

    @api.multi
    def contract_terminated(self):
        res = super().contract_terminated()
        self.filtered(lambda c: c.type == 'S')._on_sponsorship_finished()
        return res

    @api.multi
    def contract_waiting(self):
        for contract in self.with_context(lang='en_US'):
            if contract.type == 'G':
                # Activate directly if sponsorship is already active
                for line in contract.contract_line_ids:
                    sponsorship = line.sponsorship_id
                    if sponsorship.state == 'active':
                        self.env.cr.execute(
                            f"update recurring_contract set "
                            f"activation_date = current_date,is_active = True "
                            f"where id = {contract.id}")
                        self.env.clear()
            if contract.type == 'S':
                # Update the expiration date of the No Money Hold
                hold = contract.child_id.hold_id
                hold.write({
                    'expiration_date': hold.get_default_hold_expiration(
                        HoldType.NO_MONEY_HOLD)
                })
                if contract.total_amount == 0:
                    raise UserError(_(
                        "You cannot validate a sponsorship without any amount"
                    ))

        return super().contract_waiting()

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.multi
    def _on_language_changed(self):
        """ Update the preferred language in GMC. """
        action = self.env.ref('sponsorship_compassion.create_sponsorship')
        message_obj = self.env['gmc.message'].with_context(
            async_mode=False)
        for sponsorship in self.filtered(
                lambda s: s.global_id and s.state not in ('cancelled',
                                                          'terminated')):
            # Commit at each message processed
            try:
                with self.env.cr.savepoint():
                    message = message_obj.create({
                        'action_id': action.id,
                        'child_id': sponsorship.child_id.id,
                        'partner_id': sponsorship.correspondent_id.id,
                        'object_id': sponsorship.id
                    })
                    message.process_messages()
                    if message.state == 'failure':
                        failure = message.failure_reason
                        sponsorship.message_post(
                            failure, _("Language update failed."))
            except:
                logger.error(
                    "Error when updating sponsorship language. "
                    "You may be out of sync with GMC - please try again.",
                    exc_info=True
                )

    @api.multi
    def _on_change_correspondant(self, correspondent_id):
        """
        This is useful for not having to internally cancel and create
        a new commitment just to change the corresponding partner.
        It will however cancel the commitment at GMC side and create a new
        one.
        But in Odoo, we will not see the commitment has changed.
        """
        message_obj = self.env['gmc.message'].with_context(
            async_mode=False)
        cancel_action = self.env.ref(
            'sponsorship_compassion.cancel_sponsorship')

        sponsorships = self.filtered(
            lambda s: s.correspondent_id.id != correspondent_id and
            s.global_id and s.state not in ('cancelled', 'terminated'))
        sponsorships.write({
            'hold_expiration_date': self.env[
                'compassion.hold'].get_default_hold_expiration(
                HoldType.SPONSOR_CANCEL_HOLD)
        })
        cancelled_sponsorships = self.env[self._name]

        # Cancel sponsorship at GMC
        messages = message_obj
        for sponsorship in sponsorships:
            messages += message_obj.create({
                'action_id': cancel_action.id,
                'child_id': sponsorship.child_id.id,
                'partner_id': sponsorship.correspondent_id.id,
                'object_id': sponsorship.id
            })
        messages.process_messages()
        for i in range(0, len(messages)):
            if messages[i].state == 'success':
                cancelled_sponsorships += sponsorships[i]
            else:
                messages[i].unlink()
        cancelled_sponsorships.write({'global_id': False})
        return cancelled_sponsorships

    @api.multi
    def _on_correspondant_changed(self):
        """
        This is useful for not having to internally cancel and create
        a new commitment just to change the corresponding partner.
        It will however cancel the commitment at GMC side and create a new
        one.
        But in Odoo, we will not see the commitment has changed.
        """
        message_obj = self.env['gmc.message'].with_context(
            async_mode=False)
        create_action = self.env.ref(
            'sponsorship_compassion.create_sponsorship')

        # Upsert correspondents
        self.mapped('correspondent_id').upsert_constituent().process_messages()

        # Create new sponsorships at GMC
        messages = message_obj
        for sponsorship in self:
            partner = sponsorship.correspondent_id
            messages += message_obj.create({
                'action_id': create_action.id,
                'child_id': sponsorship.child_id.id,
                'partner_id': partner.id,
                'object_id': sponsorship.id
            })
        messages.process_messages()
        for i in range(0, len(messages)):
            if messages[i].state == 'failure':
                self[i].message_post(
                    messages[i].failure_reason,
                    _("The sponsorship is no more active!")
                )

    @api.multi
    def _on_sponsorship_finished(self):
        """ Called when a sponsorship is terminated or cancelled:
        Remove sponsor from the child and terminate related gift contracts.
        """
        departure = self.env.ref('sponsorship_compassion.end_reason_depart')
        for sponsorship in self:
            gift_contract_lines = self.env['recurring.contract.line'].search([
                ('sponsorship_id', '=', sponsorship.id)])
            for line in gift_contract_lines:
                contract = line.contract_id
                if len(contract.contract_line_ids) > 1:
                    line.unlink()
                else:
                    contract.contract_terminated()

            if sponsorship.global_id and \
                    sponsorship.end_reason_id != departure:
                # Cancel Sponsorship Message
                message_obj = self.env['gmc.message']
                action_id = self.env.ref(
                    'sponsorship_compassion.cancel_sponsorship').id

                message_vals = {
                    'action_id': action_id,
                    'object_id': sponsorship.id,
                    'partner_id': sponsorship.correspondent_id.id,
                    'child_id': sponsorship.child_id.id
                }
                message_obj.create(message_vals)
            elif not sponsorship.global_id:
                # Remove CreateSponsorship message.
                message_obj = self.env['gmc.message']
                action_id = self.env.ref(
                    'sponsorship_compassion.create_sponsorship').id
                message_obj.search([
                    ('action_id', '=', action_id),
                    ('state', 'in', ['new', 'failure']),
                    ('object_id', '=', sponsorship.id),
                ]).unlink()
        partners = self.mapped('partner_id') | self.mapped('correspondent_id')
        partners.update_number_sponsorships()

    @api.onchange('child_id')
    def _on_change_child_id(self):
        if self.child_id and self.child_id.hold_id:
            campaign = self.child_id.hold_id.campaign_id
            self.campaign_id = campaign

    @api.multi
    def _link_unlink_child_to_sponsor(self, vals):
        """Link/unlink child to sponsor
        """
        child_id = vals.get('child_id')
        for contract in self:
            if 'S' in contract.type and contract.child_id and \
                    contract.child_id.id != child_id:
                # Free the previously selected child
                contract.child_id.signal_workflow('release')
            if 'S' in contract.type:
                # Mark the selected child as sponsored
                self.env['compassion.child'].browse(child_id).write(
                    {'sponsor_id': vals.get('correspondent_id') or
                     contract.correspondent_id.id})

    @api.multi
    def invoice_paid(self, invoice):
        """ Prevent to reconcile invoices for fund-suspended projects
            or sponsorships older than 3 months. """
        for invl in invoice.invoice_line_ids:
            if invl.contract_id and invl.contract_id.child_id:
                contract = invl.contract_id

                # Check contract is active or terminated recently.
                if contract.state == 'cancelled':
                    raise UserError(
                        f"The contract {contract.name} is not active.")
                if contract.state == 'terminated' and contract.end_date:
                    limit = date.today() - relativedelta(days=180)
                    ended_since = fields.Date.from_string(contract.end_date)
                    if ended_since < limit:
                        raise UserError(
                            f"The contract {contract.name} is not active.")

                # Check if project allows this kind of payment.
                payment_allowed = True
                project = contract.project_id
                if invl.product_id.categ_name == SPONSORSHIP_CATEGORY:
                    payment_allowed = not project.hold_cdsp_funds or \
                        invl.due_date < project.last_reviewed_date
                if not payment_allowed:
                    raise UserError(
                        f"The project {project.fcp_id} is fund-suspended. You cannot "
                        f"reconcile invoice ({invoice.id}).")

                # Activate gift related contracts (if any)
                if 'S' in contract.type:
                    gift_contract_lines = self.env[
                        'recurring.contract.line'].search([
                            ('sponsorship_id', '=', contract.id),
                            ('contract_id.state', '=', 'waiting')
                        ])
                    gift_contract_lines.mapped('contract_id').contract_active()

                if len(contract.invoice_line_ids.filtered(
                        lambda i: i.state == 'paid')) == 1:
                    contract.partner_id.set_privacy_statement(
                        origin='first_payment')

        # Super method will activate waiting contracts
        # Only activate sponsorships with sponsorship invoice
        to_activate = self
        if invoice.invoice_type != 'sponsorship':
            to_activate -= self.filtered(lambda s: 'S' in s.type)
        super(to_activate).invoice_paid(invoice)

    @api.multi
    @api.constrains('group_id')
    def _is_a_valid_group(self):
        for contract in self.filtered(lambda c: 'S' in c.type):
            if not contract.group_id.contains_sponsorship or \
                    contract.group_id.recurring_value != 1:
                raise ValidationError(_(
                    'You should select payment option with '
                    '"1 month" as recurring value'))
        return True

    @api.multi
    def update_next_invoice_date(self):
        """ Override to force recurring_value to 1
            if contract is a sponsorship, and to bypass ORM for performance.
        """
        groups = self.mapped('group_id')
        for contract in self:
            if 'S' in contract.type:
                next_date = datetime.strptime(contract.next_invoice_date, DF)
                next_date += relativedelta(months=+1)
                next_date = next_date.strftime(DF)
            else:
                next_date = contract._compute_next_invoice_date()

            self.env.cr.execute(
                f"UPDATE recurring_contract SET next_invoice_date = {next_date}"
                f"WHERE id = {contract.id}")
        self.env.clear()
        groups._compute_next_invoice_date()
        return True

    @api.multi
    def _get_filtered_invoice_lines(self, invoice_lines):
        # Exclude gifts from being cancelled
        res = invoice_lines.filtered(
            lambda invl: invl.contract_id.id in self.ids and
            invl.product_id.categ_name != GIFT_CATEGORY)
        return res

    def hold_gifts(self):
        """ Hook for holding gifts. """
        pass

    def reactivate_gifts(self):
        """ Hook for reactivating gifts. """
        pass

    @api.multi
    def _filter_clean_invoices(self, since_date, to_date):
        """ Exclude gifts from clean invoice method. """
        invl_search = super()._filter_clean_invoices(
            since_date, to_date
        )
        invl_search.append(('product_id.categ_name', '!=', GIFT_CATEGORY))
        return invl_search
