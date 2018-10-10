# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging
from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.queue_job.job import job, related_action

logger = logging.getLogger(__name__)


class ContractGroup(models.Model):
    _inherit = 'recurring.contract.group'

    def _get_gen_states(self):
        return ['active', 'waiting']


class RecurringContract(models.Model):
    _inherit = ['recurring.contract', 'utm.mixin']
    _order = 'id desc'
    _rec_name = 'name'
    _name = 'recurring.contract'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    child_id = fields.Many2one(
        'compassion.child', 'Sponsored child', readonly=True, copy=False,
        states={'draft': [('readonly', False)],
                'waiting': [('readonly', False)],
                'mandate': [('readonly', False)]}, ondelete='restrict',
        track_visibility='onchange')
    project_id = fields.Many2one('compassion.project', 'Project',
                                 related='child_id.project_id')
    child_name = fields.Char(
        'Sponsored child name', related='child_id.name', readonly=True)
    child_code = fields.Char(
        'Sponsored child code', related='child_id.local_id', readonly=True)
    activation_date = fields.Date(readonly=True, copy=False)
    is_active = fields.Boolean(
        'Contract Active', compute='_compute_active', store=True,
        help="It indicates that the first invoice has been paid and the "
             "contract was activated.")
    # Field used for identifying gifts from sponsor
    commitment_number = fields.Integer(
        'Partner Contract Number', required=True, copy=False,
        oldname='num_pol_ga'
    )
    end_reason = fields.Selection('get_ending_reasons', copy=False)
    months_paid = fields.Integer(compute='_compute_months_paid')
    origin_id = fields.Many2one(
        'recurring.contract.origin', 'Origin', ondelete='restrict',
        track_visibility='onchange')

    parent_id = fields.Many2one(
        'recurring.contract', 'Previous sponsorship',
        track_visibility='onchange', index=True, copy=False)

    sub_sponsorship_id = fields.Many2one(
        'recurring.contract', 'sub sponsorship', readonly=True, copy=False)

    name = fields.Char(compute='_compute_name', store=True)
    partner_id = fields.Many2one(
        'res.partner', 'Partner', required=True,
        readonly=False, states={'terminated': [('readonly', True)]},
        ondelete='restrict', track_visibility='onchange')
    type = fields.Selection('_get_type', required=True, default='O')
    group_freq = fields.Char(
        string='Payment frequency', compute='_compute_frequency',
        readonly=True)
    sponsorship_line_id = fields.Integer(
        help='Identifies the active sponsorship line of a sponsor.'
             'When sponsorship is ended but a SUB is made, the SUB will have'
             'the same line id. Only new sponsorships will have new ids.'
    )
    contract_duration = fields.Integer(compute='_compute_contract_duration',
                                       help='Contract duration in days')

    _sql_constraints = [('parent_id_unique',
                         'UNIQUE(parent_id)',
                         'Unfortunately this sponsorship is already used,'
                         'please choose a unique one'),
                        ('sub_sponsorship_id_unique',
                         'UNIQUE(sub_sponsorship_id)',
                         'Unfortunately this sponsorship is already'
                         'used, please choose a unique one')]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def _get_states(self):
        """ Add a waiting and a cancelled state """
        states = super(RecurringContract, self)._get_states()
        states.insert(1, ('waiting', _('Waiting Payment')))
        states.insert(len(states), ('cancelled', _('Cancelled')))
        return states

    @api.multi
    @api.depends('partner_id', 'partner_id.ref', 'child_id',
                 'child_id.local_id')
    def _compute_name(self):
        """ Gives a friendly name for a sponsorship """
        for contract in self:
            if contract.partner_id.ref or contract.reference:
                name = contract.partner_id.ref or contract.reference
                if contract.child_id:
                    name += ' - ' + contract.child_code
                elif contract.contract_line_ids:
                    name += ' - ' + contract.contract_line_ids[
                        0].product_id.name
                contract.name = name

    @api.multi
    @api.depends('activation_date', 'state')
    def _compute_active(self):
        for contract in self:
            contract.is_active = bool(contract.activation_date) and \
                contract.state not in ('terminated', 'cancelled')

    def get_ending_reasons(self):
        """Returns all the ending reasons of sponsorships"""
        return [
            ('2', _("Mistake from our staff")),
            ('3', _("Death of partner")),
            ('4', _("Moved to foreign country")),
            ('5', _("Not satisfied")),
            ('6', _("Doesn't pay")),
            ('8', _("Personal reasons")),
            ('9', _("Never paid")),
            ('12', _("Financial reasons")),
            ('25', _("Not given")),
        ]

    def _get_type(self):
        return [('O', _('General'))]

    @api.multi
    def _compute_frequency(self):
        frequencies = {
            '1 month': _('Monthly'),
            '2 month': _('Bimonthly'),
            '3 month': _('Quarterly'),
            '4 month': _('Four-monthly'),
            '6 month': _('Bi-annual'),
            '12 month': _('Annual'),
            '1 year': _('Annual'),
        }
        for contract in self:
            if contract.type == 'S':
                recurring_value = contract.group_id.advance_billing_months
                recurring_unit = 'month'
            else:
                recurring_value = contract.group_id.recurring_value
                recurring_unit = contract.group_id.recurring_unit
            frequency = "{0} {1}".format(recurring_value, recurring_unit)
            if frequency in frequencies:
                frequency = frequencies[frequency]
            else:
                frequency = _('every') + ' ' + frequency.lower()
            contract.group_freq = frequency

    @api.multi
    def _compute_months_paid(self):
        """This is a query returning the number of months paid for a
        sponsorship."""
        self._cr.execute(
            "SELECT c.id as contract_id, "
            "12 * (EXTRACT(year FROM next_invoice_date) - "
            "      EXTRACT(year FROM current_date))"
            " + EXTRACT(month FROM c.next_invoice_date) - 1"
            " - COALESCE(due.total, 0) as paidmonth "
            "FROM recurring_contract c left join ("
            # Open invoices to find how many months are due
            "   select contract_id, count(distinct invoice_id) as total "
            "   from account_invoice_line l join product_product p on "
            "       l.product_id = p.id "
            "   where state='open' and "
            # Exclude gifts from count
            "   categ_name != 'Sponsor gifts'"
            "   group by contract_id"
            ") due on due.contract_id = c.id "
            "WHERE c.id = ANY (%s)",
            (self.ids,)
        )
        res = self._cr.dictfetchall()
        dict_contract_id_paidmonth = {
            row['contract_id']: int(row['paidmonth'] or 0) for row in res}
        for contract in self:
            contract.months_paid = dict_contract_id_paidmonth.get(contract.id)

    @api.multi
    def _compute_contract_duration(self):
        for contract in self:
            if not contract.activation_date:
                contract.contract_duration = 0
            else:
                contract_start_date = fields.Date.from_string(
                    contract.activation_date)
                end_date = fields.Date.from_string(
                    contract.end_date) if contract.end_date else date.today()
                contract.contract_duration = (
                    end_date - contract_start_date).days

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        if 'commitment_number' not in vals:
            partner_id = vals.get('partner_id')
            if partner_id:
                other_nums = self.search([
                    ('partner_id', '=', partner_id)
                ]).mapped('commitment_number')
                vals['commitment_number'] = max(other_nums or [-1]) + 1
            else:
                vals['commitment_number'] = 1

        new_sponsorship = super(RecurringContract, self).create(vals)

        # Set the sub_sponsorship_id in the current parent_id and take
        # sponsorship line id
        if 'parent_id' in vals and vals['parent_id']:
            sponsorship = self.env['recurring.contract'].\
                browse(vals['parent_id'])

            sponsorship.sub_sponsorship_id = new_sponsorship
            new_sponsorship.sponsorship_line_id =\
                sponsorship.sponsorship_line_id

        return new_sponsorship

    @api.multi
    def write(self, vals):
        """ Perform various checks when a contract is modified. """

        # Change the sub_sponsorship_id value in the previous parent_id
        if 'parent_id' in vals:
            self.mapped('parent_id').write({'sub_sponsorship_id': False})

        # Write the changes
        res = super(RecurringContract, self).write(vals)

        # Set the sub_sponsorship_id in the current parent_id
        if 'parent_id' in vals:
            for sponsorship in self.filtered('parent_id'):
                parent = sponsorship.parent_id
                parent.sub_sponsorship_id = sponsorship
                sponsorship.sponsorship_line_id = parent.sponsorship_line_id

        if 'group_id' in vals or 'partner_id' in vals:
            self._on_group_id_changed()

        return res

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def invoice_unpaid(self, invoice):
        """ Hook when invoice is unpaid """
        pass

    @api.multi
    def invoice_paid(self, invoice):
        """ Activate contract if it is waiting for payment. """
        activate_contracts = self.filtered(lambda c: c.state == 'waiting')
        activate_contracts.signal_workflow('contract_active')

    @api.multi
    def force_activation(self):
        """ Used to transition sponsorships in active state. """
        self.signal_workflow('contract_validated')
        self.signal_workflow('contract_active')
        logger.info("Contracts " + str(self.ids) + " activated.")
        return True

    def clean_invoices_paid(self, since_date, to_date):
        """
        Unreconcile paid invoices in the given period, so that they
        can be cleaned with the clean_invoices process.
        :param since_date: clean invoices with date greater than this
        :param to_date: clean invoices with date lower than this
        :return: invoices cleaned that contained other contracts than the
                 the ones we are cleaning.
        """
        # Find all paid invoice lines after the given date
        inv_line_obj = self.env['account.invoice.line']
        invl_search = self._filter_clean_invoices(since_date, to_date)
        inv_lines = inv_line_obj.search(invl_search)
        move_lines = inv_lines.mapped('invoice_id.move_id.line_ids').filtered(
            'reconciled')
        reconciles = inv_lines.mapped(
            'invoice_id.payment_move_line_ids.full_reconcile_id')

        # Unreconcile paid invoices
        move_lines |= reconciles.mapped('reconciled_line_ids')
        move_lines.remove_move_reconcile()

        return move_lines.mapped('invoice_id.invoice_line_ids').filtered(
            lambda l: l.contract_id not in self).mapped('invoice_id')

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.onchange('partner_id')
    def on_change_partner_id(self):
        """ On partner change, we set the new pol_number
        (for gift identification). """
        super(RecurringContract, self).on_change_partner_id()
        num_contracts = self.search_count(
            [('partner_id', '=', self.partner_id.id)])

        self.commitment_number = num_contracts

    @api.onchange('parent_id')
    def on_change_parent_id(self):
        """ If a previous sponsorship is selected, the origin should be
        SUB Sponsorship. """
        if self.parent_id:
            self.origin_id = self.parent_id.origin_id.id

    @api.multi
    def open_contract(self):
        """ Used to bypass opening a contract in popup mode from
        res_partner view. """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contract',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'target': 'current',
            'context': self.with_context(default_type=self.type).env.context
        }

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    @api.multi
    def contract_active(self):
        self.filtered(lambda c: not c.is_active).write({
            'activation_date': fields.Date.today()
        })
        self.write({'state': 'active'})
        last_line_id = self.search(
            [('sponsorship_line_id', '!=', False)],
            order='sponsorship_line_id desc',
            limit=1
        ).sponsorship_line_id

        # Write payment term in partner property and sponsorship line id
        for contract in self:
            contract.partner_id.customer_payment_mode_id = \
                contract.payment_mode_id
            if contract.child_id and not contract.sponsorship_line_id:
                last_line_id += 1
                contract.sponsorship_line_id = last_line_id

        # Cancel the old invoices if a contract is activated
        delay = datetime.now() + relativedelta(seconds=30)
        self.with_delay(eta=delay).cancel_old_invoices()
        return True

    @api.multi
    def contract_cancelled(self):
        self.write({
            'state': 'cancelled',
            'end_date': fields.Datetime.now()
        })
        self.clean_invoices()
        return True

    @api.multi
    def contract_terminated(self):
        self.write({
            'state': 'terminated',
            'end_date': fields.Datetime.now()
        })
        self.clean_invoices()
        return True

    @api.multi
    def contract_waiting(self):
        return self.write({
            'state': 'waiting',
            'start_date': fields.Datetime.now()
        })

    @api.multi
    def action_cancel_draft(self):
        """ Set back a cancelled contract to draft state. """
        update_sql = "UPDATE recurring_contract " \
            "SET state='draft', end_date=NULL, activation_date=NULL, " \
            "start_date=CURRENT_DATE, end_reason=NULL"
        for contract in self.filtered(lambda c: c.state == 'cancelled'):
            query = update_sql
            if contract.child_id and not contract.child_id.is_available:
                query += ', child_id = NULL'
            query += " WHERE id = %s"
            self.env.cr.execute(query, [contract.id])
            contract.delete_workflow()
            contract.create_workflow()
            self.env.invalidate_all()
        return True

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.multi
    def _on_change_next_invoice_date(self, new_invoice_date):
        """ Disable rewind check on draft and mandate contracts. """
        contracts = self.filtered(
            lambda c: c.state not in ('draft', 'mandate'))
        super(RecurringContract, contracts)._on_change_next_invoice_date(
            new_invoice_date)

    def _get_filtered_invoice_lines(self, invoice_lines):
        return invoice_lines.filtered(lambda l: l.contract_id.id in self.ids)

    @api.multi
    @job(default_channel='root.recurring_invoicer')
    @related_action(action='related_action_contract')
    def _clean_invoices(self, since_date=None, to_date=None,
                        keep_lines=None, clean_invoices_paid=True):
        """ Clean invoices
        Take into consideration when the sponsor has paid in advance,
        so that we cancel/modify the paid invoices and let the user decide
        what to do with the payment.
        :param since_date: optional date from which invoices will be cleaned
        :param to_date: optional date limit for invoices we want to clean
        :param keep_lines: set to true to avoid deleting invoice lines
        :param clean_invoices_paid: set to true to unreconcile paid invoices
                                    and clean them as well.
        :return: invoices cleaned (which should be in cancel state)
        """
        if clean_invoices_paid:
            sponsorships = self.filtered(lambda s: s.type == 'S')
            paid_invoices = sponsorships.clean_invoices_paid(since_date,
                                                             to_date)

        invoices = super(RecurringContract, self)._clean_invoices(
            since_date, to_date, keep_lines)
        if clean_invoices_paid:
            paid_invoices.reconcile_after_clean()
        return invoices

    @job(default_channel='root.recurring_invoicer')
    @related_action(action='related_action_contract')
    def cancel_old_invoices(self):
        """Cancel the old open invoices of a contract
           which are older than the first paid invoice of contract.
           If the invoice has only one contract -> cancel
           Else -> draft to modify the invoice and validate
        """
        invoice_line_obj = self.env['account.invoice.line']
        paid_invl = invoice_line_obj.search([
            ('contract_id', 'in', self.ids),
            ('state', '=', 'paid')], order='due_date asc', limit=1)
        invoice_lines = invoice_line_obj.search([
            ('contract_id', 'in', self.ids),
            ('state', '=', 'open'),
            ('due_date', '<', paid_invl.due_date)])

        invoices = invoice_lines.mapped('invoice_id')

        for invoice in invoices:
            invoice_lines = invoice.invoice_line_ids

            inv_lines = self._get_filtered_invoice_lines(invoice_lines)

            if len(inv_lines) == len(invoice_lines):
                invoice.action_invoice_cancel()
            else:
                invoice.action_invoice_cancel()
                invoice.action_invoice_draft()
                invoice.env.invalidate_all()
                inv_lines.unlink()
                invoice.action_invoice_open()

    def _clean_error(self):
        raise UserError(
            _('The sponsor has already paid in advance for this '
              'sponsorship, but the system was unable to automatically '
              'cancel the invoices. Please refer to an accountant for '
              'changing the attribution of his payment before cancelling '
              'the sponsorship.'))

    @api.multi
    def _reset_open_invoices_job(self):
        """Clean the open invoices in order to generate new invoices.
        This can be useful if contract was updated when active."""
        invoices_canceled = self._clean_invoices(clean_invoices_paid=False)
        if invoices_canceled:
            invoice_obj = self.env['account.invoice']
            inv_update_ids = set()
            for contract in self:
                # If some invoices are left cancelled, we update them
                # with new contract information and validate them
                cancel_invoices = invoice_obj.search([
                    ('state', '=', 'cancel'),
                    ('id', 'in', invoices_canceled.ids)])
                if cancel_invoices:
                    inv_update_ids.update(cancel_invoices.ids)
                    cancel_invoices.action_invoice_draft()
                    cancel_invoices.env.invalidate_all()
                    contract._update_invoice_lines(cancel_invoices)
                # If no invoices are left in cancel state, we rewind
                # the next_invoice_date for the contract to generate again
                else:
                    contract.rewind_next_invoice_date()
                    invoicer = contract.group_id._generate_invoices()
                    if not invoicer.invoice_ids:
                        invoicer.unlink()
            # Validate again modified invoices
            validate_invoices = invoice_obj.browse(list(inv_update_ids))
            validate_invoices.action_invoice_open()
        return True

    @api.multi
    def _filter_clean_invoices(self, since_date, to_date):
        """ Construct filter domain to be passed on method
        clean_invoices_paid, which will determine which invoice lines will
        be removed from invoices. """
        if not since_date:
            since_date = fields.Date.today()
        invl_search = [('contract_id', 'in', self.ids), ('state', '=', 'paid'),
                       ('due_date', '>=', since_date)]
        if to_date:
            invl_search.append(('due_date', '<=', to_date))
        return invl_search

    def _on_group_id_changed(self):
        """Remove lines of open invoices and generate them again
        """
        self._reset_open_invoices_job()
        for contract in self:
            # Update next_invoice_date of group if necessary
            if contract.group_id.next_invoice_date:
                next_invoice_date = fields.Datetime.from_string(
                    contract.next_invoice_date)
                group_date = fields.Datetime.from_string(
                    contract.group_id.next_invoice_date)
                if group_date > next_invoice_date:
                    contract.group_id._compute_next_invoice_date()
