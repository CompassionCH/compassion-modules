# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import models, fields, api, netsvc, exceptions, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
logger = logging.getLogger(__name__)


class recurring_contract(models.Model):
    _inherit = "recurring.contract"
    _order = 'start_date desc'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    child_id = fields.Many2one(
        'compassion.child', 'Sponsored child', readonly=True, copy=False,
        states={'draft': [('readonly', False)],
                'waiting': [('readonly', False)],
                'mandate': [('readonly', False)]}, ondelete='restrict',
        track_visibility='onchange')
    child_name = fields.Char(
        'Sponsored child name', related='child_id.name', readonly=True)
    child_code = fields.Char(
        'Sponsored child code', related='child_id.code', readonly=True)
    partner_codega = fields.Char(
        'Partner ref', related='partner_id.ref', readonly=True)
    activation_date = fields.Date(readonly=True, copy=False)
    # Add a waiting and waiting mandate states
    state = fields.Selection(selection=[
        ('draft', _('Draft')),
        ('mandate', _('Waiting Mandate')),
        ('waiting', _('Waiting Payment')),
        ('active', _('Active')),
        ('terminated', _('Terminated')),
        ('cancelled', _('Cancelled'))])
    is_active = fields.Boolean(
        'Contract Active', compute='_set_active', store=True,
        help="It indicates that the first invoice has been paid and the "
             "contract was activated.")
    # Field used for identifying gifts from sponsor (because of bad GP)
    num_pol_ga = fields.Integer(
        'Partner Contract Number', required=True)
    end_reason = fields.Selection('get_ending_reasons')
    end_date = fields.Date(readonly=True, track_visibility='onchange')
    origin_id = fields.Many2one(
        'recurring.contract.origin', 'Origin', ondelete='restrict',
        track_visibility='onchange')
    channel = fields.Selection('_get_channels')
    parent_id = fields.Many2one(
        'recurring.contract', 'Previous sponsorship',
        track_visibility='onchange')
    has_mandate = fields.Boolean(compute='_set_has_mandate')
    name = fields.Char(readonly=True)
    partner_id = fields.Many2one(
        'res.partner', 'Partner', required=True,
        readonly=False, states={'terminated': [('readonly', True)]},
        ondelete='restrict', track_visibility='onchange')
    type = fields.Selection('_get_type', required=True)
    group_freq = fields.Char(
        'Frequency', compute='_set_frequency', store=True, readonly=True)

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.one
    @api.depends('state')
    def _set_active(self):
        self.is_active = bool(self.activation_date) and \
            self.state not in ('terminated', 'cancelled')

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

    def _get_channels(self):
        """Returns the available channel through the new sponsor
        reached Compassion.
        """
        return [
            ('postal', _("By mail")),
            ('direct', _("Direct")),
            ('email', _("By e-mail")),
            ('internet', _("From the website")),
            ('phone', _("By phone")),
            ('payment', _("Payment")),
        ]

    @api.one
    def _set_has_mandate(self):
        # Search for an existing valid mandate
        count = self.env['account.banking.mandate'].search_count([
            ('partner_id', '=', self.partner_id.id),
            ('state', '=', 'valid')])
        self.has_mandate = bool(count)

    def _get_type(self):
        return [('O', _('General'))]

    @api.one
    @api.depends('group_id.recurring_unit', 'group_id.recurring_value')
    def _set_frequency(self):
        frequencies = {
            '1 month': 'Monthly',
            '2 month': 'Bimonthly',
            '3 month': 'Quarterly',
            '4 month': 'Four-monthly',
            '6 month': 'Bi-annual',
            '12 month': 'Annual',
            '1 year': 'Annual',
        }
        recurring_value = self.group_id.recurring_value
        recurring_unit = self.group_id.recurring_unit
        frequency = "{0} {1}".format(recurring_value, recurring_unit)
        if frequency in frequencies:
            frequency = frequencies[frequency]
        self.group_freq = frequency

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        if 'num_pol_ga' not in vals:
            partner_id = vals.get('partner_id')
            if partner_id:
                vals['num_pol_ga'] = self.search_count([
                    ('partner_id', '=', partner_id)])
        return super(recurring_contract, self).create(vals)

    @api.multi
    @api.depends('partner_id', 'child_id')
    def name_get(self):
        """ Gives a friendly name for a sponsorship """
        res = []
        for contract in self:
            name = contract.partner_id.ref or contract.reference
            if contract.child_id:
                name += ' - ' + contract.child_code
            elif contract.contract_line_ids:
                name += ' - ' + contract.contract_line_ids[0].product_id.name
            res.append((contract.id, name))
        return res

    @api.one
    def copy(self, default=None):
        if default is None:
            default = dict()
        default.update({
            'num_pol_ga': self.num_pol_ga + 1
        })
        return super(recurring_contract, self).copy(default)

    @api.multi
    def write(self, vals):
        """ Perform various checks when a contract is modified. """
        if 'group_id' in vals:
            self._on_change_group_id(vals['group_id'])

        # Write the changes
        res = super(recurring_contract, self).write(vals)

        if 'group_id' in vals or 'partner_id' in vals:
            self._on_group_id_changed()

        return res

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def invoice_unpaid(self, invoice):
        wf_service = netsvc.LocalService('workflow')
        cr = self.env.cr
        uid = self.env.user.id
        for contract in self:
            wf_service.trg_validate(
                uid, self._name, contract.id, 'contract_activation_cancelled',
                cr)

    def invoice_paid(self, invoice):
        """ Activate contract if it is waiting for payment. """
        activate_contracts = self.filtered(lambda c: c.state == 'waiting')
        # Cancel the old invoices if a contract is activated
        activate_contracts._cancel_old_invoices(
            invoice.partner_id.id, invoice.date_invoice)

        wf_service = netsvc.LocalService('workflow')
        cr = self.env.cr
        uid = self.env.user.id
        for contract in activate_contracts:
            wf_service.trg_validate(
                uid, self._name, contract.id,
                'contract_active', cr)
            logger.info("Contract " + str(id) + " activated.")

    @api.one
    def force_activation(self):
        """ Used to transition sponsorships in active state. """
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(self.env.user.id, self._name, self.id,
                                'contract_validated', self.env.cr)
        wf_service.trg_validate(self.env.user.id, self._name, self.id,
                                'contract_active', self.env.cr)
        logger.info("Contract " + str(self.id) + " activated.")
        return True

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.onchange('partner_id')
    def on_change_partner_id(self):
        """ On partner change, we set the new pol_number
        (for gift identification). """
        super(recurring_contract, self).on_change_partner_id()
        num_contracts = self.search_count(
            [('partner_id', '=', self.partner_id.id)])

        self.num_pol_ga = num_contracts

    @api.onchange('parent_id')
    def on_change_parent_id(self):
        """ If a previous sponsorship is selected, the origin should be
        SUB Sponsorship. """
        if self.parent_id:
            origin = self.env['recurring.contract.origin'].search(
                [('type', '=', 'sub')])[0]
            self.origin_id = origin.id

    @api.onchange('group_id')
    def on_change_group_id(self):
        """ Compute next invoice_date """
        current_date = datetime.today()
        is_active = False

        if self.state not in ('draft', 'mandate') and self.next_invoice_date:
            is_active = True
            current_date = datetime.strptime(self.next_invoice_date, DF)

        if self.group_id:
            contract_group = self.group_id
            if contract_group.next_invoice_date:
                next_group_date = datetime.strptime(
                    contract_group.next_invoice_date, DF)
                next_invoice_date = current_date.replace(
                    day=next_group_date.day)
            else:
                next_invoice_date = current_date.replace(day=1)
            payment_term = contract_group.payment_term_id.name
        else:
            next_invoice_date = current_date.replace(day=1)
            payment_term = ''

        if current_date.day > 15 or (
                payment_term in ('LSV', 'Postfinance') and not is_active):
            next_invoice_date = next_invoice_date + relativedelta(months=+1)
        self.next_invoice_date = next_invoice_date.strftime(DF)

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
            'context': self.env.with_context(default_type=self.type).context
        }

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    @api.multi
    def contract_active(self):
        self.write({
            'activation_date': datetime.today().strftime(DF),
            'state': 'active'})
        return True

    @api.multi
    def contract_cancelled(self):
        self.write({'state': 'cancelled'})
        self.clean_invoices()
        return True

    @api.multi
    def contract_terminated(self):
        self.write({'state': 'terminated'})
        self.clean_invoices()
        return True

    @api.multi
    def contract_waiting_mandate(self):
        self.write({'state': 'mandate'})
        return True

    @api.multi
    def contract_validation(self):
        """Only for making the tests successful."""
        return True

    @api.one
    def contract_waiting(self):
        vals = {'state': 'waiting'}
        payment_term = self.group_id.payment_term_id.name
        if self.type == 'S' and ('LSV' in payment_term or
                                 'Postfinance' in payment_term):
            # Recompute next_invoice_date
            today = datetime.today()
            next_invoice_date = datetime.strptime(
                self.next_invoice_date, DF).replace(month=today.month,
                                                    year=today.year)
            if today.day > 15 and next_invoice_date.day < 15:
                next_invoice_date = next_invoice_date + relativedelta(
                    months=+1)
            vals['next_invoice_date'] = next_invoice_date.strftime(DF)

        self.write(vals)
        return True

    @api.one
    def action_cancel_draft(self):
        """ Set back a cancelled contract to draft state. """
        wf_service = netsvc.LocalService('workflow')
        update_sql = "UPDATE recurring_contract SET state='draft', "\
            "end_date=NULL, activation_date=NULL, start_date=CURRENT_DATE"
        cr = self.env.cr
        uid = self.env.user.id
        if self.state == 'cancelled':
            if self.child_id and not self.child_id.is_available:
                update_sql += ', child_id = NULL'
            cr.execute(update_sql + " WHERE id = %s", [self.id])
            wf_service.trg_delete(uid, self._name, self.id, cr)
            wf_service.trg_create(uid, self._name, self.id, cr)
            self.env.invalidate_all()
        return True

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.one
    def _on_change_next_invoice_date(self, new_invoice_date):
        if self.state not in ('draft', 'mandate'):
            super(recurring_contract, self)._on_change_next_invoice_date(
                new_invoice_date)

    def _get_filtered_invoice_lines(self, invoice_lines):
        return invoice_lines.filtered(lambda l: l.contract_id.id in self.ids)

    def _cancel_old_invoices(self, partner_id, date_invoice):
        """
            Cancel the open invoices of a contract
            which are older than a given date.
            If the invoice has only one contract -> cancel
            Else -> draft to modify the invoice and validate
        """
        invoice_line_obj = self.env['account.invoice.line']
        invoice_lines = invoice_line_obj.search([
            ('contract_id', 'in', self.ids),
            ('state', '=', 'open'),
            ('due_date', '<', date_invoice)])

        invoices = invoice_lines.mapped('invoice_id')

        wf_service = netsvc.LocalService('workflow')
        for invoice in invoices:
            invoice_lines = invoice.invoice_line

            inv_lines = self._get_filtered_invoice_lines(
                invoice_lines)

            if len(inv_lines) == len(invoice_lines):
                wf_service.trg_validate(
                    self.env.user.id, 'account.invoice',
                    invoice.id, 'invoice_cancel', self.env.cr)
            else:
                invoice.action_cancel_draft()
                inv_lines.unlink()

                wf_service.trg_validate(
                    self.env.user.id, 'account.invoice',
                    invoice.id, 'invoice_open', self.env.cr)

    @api.one
    def _update_invoice_lines(self, invoices):
        super(recurring_contract, self)._update_invoice_lines(invoices)
        # Update bvr_reference of invoices
        invoices.write({
            'bvr_reference': self.group_id.bvr_reference})

    def _clean_error(self):
        raise exceptions.Warning(
            _('Cancel Invoice Error'),
            _('The sponsor has already paid in advance for this '
              'sponsorship, but the system was unable to automatically '
              'cancel the invoices. Please refer to an accountant for '
              'changing the attribution of his payment before cancelling '
              'the sponsorship.'))

    def _reset_open_invoices(self):
        """Clean the open invoices in order to generate new invoices.
        This can be useful if contract was updated when active."""
        invoices_canceled = super(recurring_contract, self).clean_invoices()
        if invoices_canceled:
            invoice_obj = self.env['account.invoice']
            inv_update_ids = set()
            for contract in self:
                # If some invoices are left cancelled, we update them
                # with new contract information and validate them
                cancel_invoices = invoice_obj.search([
                    ('state', '=', 'cancel'),
                    ('id', 'in', list(invoices_canceled))])
                if cancel_invoices:
                    inv_update_ids.update(cancel_invoices.ids)
                    cancel_invoices.action_cancel_draft()
                    contract._update_invoice_lines(cancel_invoices)
                # If no invoices are left in cancel state, we rewind
                # the next_invoice_date for the contract to generate again
                else:
                    contract.rewind_next_invoice_date()
                    invoicer_id = contract.group_id.generate_invoices()
                    invoicer = self.env['recurring.invoicer'].browse(
                        invoicer_id)
                    if invoicer.invoice_ids:
                        invoicer.validate_invoices()
                    else:
                        invoicer.unlink()
            # Validate again modified invoices
            if inv_update_ids:
                wf_service = netsvc.LocalService('workflow')
                for invoice_id in inv_update_ids:
                    wf_service.trg_validate(
                        self.env.user.id, 'account.invoice', invoice_id,
                        'invoice_open', self.env.cr)
        return True

    def _on_change_group_id(self, group_id):
        """ Change state of contract if payment is changed to/from LSV or DD.
        """
        wf_service = netsvc.LocalService('workflow')
        group = self.env['recurring.contract.group'].browse(
            group_id)
        payment_name = group.payment_term_id.name
        if 'LSV' in payment_name or 'Postfinance' in payment_name:
            for contract in self:
                wf_service.trg_validate(
                    self.env.user.id, self._name, contract.id,
                    'will_pay_by_lsv_dd', self.env.cr)
        else:
            # Check if old payment_term was LSV or DD
            for contract in self:
                payment_name = contract.group_id.payment_term_id.name
                if 'LSV' in payment_name or 'Postfinance' in payment_name:
                    wf_service.trg_validate(
                        self.env.user.id, 'recurring.contract', contract.id,
                        'mandate_validated', self.env.cr)

    def _on_group_id_changed(self):
        """Remove lines of open invoices and generate them again
        """
        self._reset_open_invoices()
        for contract in self:
            # Update next_invoice_date of group if necessary
            if contract.group_id.next_invoice_date:
                next_invoice_date = datetime.strptime(
                    contract.next_invoice_date, DF)
                group_date = datetime.strptime(
                    contract.group_id.next_invoice_date, DF)
                if group_date > next_invoice_date:
                    # This will trigger group_date computation
                    contract.write({
                        'next_invoice_date': contract.next_invoice_date})
