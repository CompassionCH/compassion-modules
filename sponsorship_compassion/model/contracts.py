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

from openerp.osv import orm, fields
from openerp import netsvc
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging

logger = logging.getLogger(__name__)


class recurring_contract(orm.Model):
    _inherit = "recurring.contract"

    ################################
    #        FIELDS METHODS        #
    ################################
    def _active(self, cr, uid, ids, field_name, args, context=None):
        # Dummy function that sets the active flag.
        self._on_contract_active(cr, uid, ids, context=context)
        return {id: True for id in ids}

    def _get_contract_from_invoice(invoice_obj, cr, uid, invoice_ids,
                                   context=None):
        self = invoice_obj.pool.get('recurring.contract')
        res = set()
        # Read data in english
        if context is None:
            context = {}
        ctx = context.copy()
        ctx['lang'] = 'en_US'
        for invoice in invoice_obj.browse(cr, uid, invoice_ids, ctx):
            if invoice.state == 'paid':
                self._invoice_paid(cr, uid, invoice, ctx)
                last_pay_date = max([move_line.date
                                     for move_line in invoice.payment_ids
                                     if move_line.credit > 0] or [0])
                for invoice_line in invoice.invoice_line:
                    contract = invoice_line.contract_id
                    if contract.id not in res and (contract.state == 'waiting'
                                                   and last_pay_date):
                        # Activate the contract and set the
                        # activation_date
                        res.add(contract.id)
                        contract.write({
                            'activation_date': datetime.today().strftime(DF)})

        return list(res)

    def _is_fully_managed(self, cr, uid, ids, field_name, arg, context):
        """Tells if the correspondent and the payer is the same person."""
        res = dict()
        for contract in self.browse(cr, uid, ids, context=context):
            res[contract.id] = contract.partner_id == contract.correspondant_id
        return res

    def get_ending_reasons(self, cr, uid, context=None):
        """Returns all the ending reasons of sponsorships"""
        return [
            ('1', _("Depart of child")),
            ('2', _("Mistake from our staff")),
            ('3', _("Death of sponsor")),
            ('4', _("Moved to foreign country")),
            ('5', _("Not satisfied")),
            ('6', _("Doesn't pay")),
            ('8', _("Personal reasons")),
            ('9', _("Never paid")),
            ('10', _("Subreject")),
            ('11', _("Exchange of sponsor")),
            ('12', _("Financial reasons")),
            ('25', _("Not given")),
        ]

    def _get_channels(self, cr, uid, context=None):
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

    def _has_mandate(self, cr, uid, ids, field_name, args, context=None):
        # Search for an existing valid mandate
        res = dict()
        for contract in self.browse(cr, uid, ids, context):
            count = self.pool.get('account.banking.mandate').search(cr, uid, [
                ('partner_id', '=', contract.partner_id.id),
                ('state', '=', 'valid')], count=True, context=context)
            res[contract.id] = bool(count)
        return res

    def _name_get(self, cr, uid, ids, field_name, args, context=None):
        return {c[0]: c[1] for c in self.name_get(cr, uid, ids, context)}

    def _get_standard_lines(self, cr, uid, context=None):
        """ Select Sponsorship and General Fund by default """
        ctx = {'lang': 'en_US'}
        res = []
        product_obj = self.pool.get('product.product')
        sponsorship_id = product_obj.search(
            cr, uid, [('name', '=', 'Sponsorship')], context=ctx)[0]
        gen_id = product_obj.search(
            cr, uid, [('name', '=', 'General Fund')], context=ctx)[0]
        sponsorship_vals = {
            'product_id': sponsorship_id,
            'quantity': 1,
            'amount': 42,
            'subtotal': 42
        }
        gen_vals = {
            'product_id': gen_id,
            'quantity': 1,
            'amount': 8,
            'subtotal': 8
        }
        res.append([0, 6, sponsorship_vals])
        res.append([0, 6, gen_vals])
        return res

    ###########################
    #        New Fields       #
    ###########################
    _columns = {
        'child_id': fields.many2one(
            'compassion.child', _('Sponsored child'), readonly=True,
            states={'draft': [('readonly', False)]}, ondelete='restrict'),
        'child_name': fields.related(
            'child_id', 'name', string=_('Sponsored child name'),
            readonly=True, type='char'),
        'child_code': fields.related(
            'child_id', 'code', string=_('Sponsored child code'),
            readonly=True, type='char'),
        'partner_codega': fields.related(
            'partner_id', 'ref', string=_('Partner ref'), readonly=True,
            type='char'),
        # This field is only for the middleware testing purpose.
        # In the future, the type will be identified in another way.
        'type': fields.selection([
            ('ChildSponsorship', 'Sponsorship'),
            ('ChildCorrespondenceSponsorship', 'Correspondence')],
            _("Type of sponsorship")),
        'correspondant_id': fields.many2one(
            'res.partner', _('Correspondant'), required=True, readonly=True,
            states={'draft': [('readonly', False)]}),
        'activation_date': fields.date(
            _('Activation date'), readonly=True),
        # Add a waiting and waiting mandate states
        'state': fields.selection([
            ('draft', _('Draft')),
            ('mandate', _('Waiting Mandate')),
            ('waiting', _('Waiting Payment')),
            ('active', _('Active')),
            ('terminated', _('Terminated')),
            ('cancelled', _('Cancelled'))], _('Status'), select=True,
            readonly=True, track_visibility='onchange',
            help=_(" * The 'Draft' status is used when a user is encoding a "
                   "new and unconfirmed Contract.\n"
                   " * The 'Waiting' status is used when the Contract is "
                   " confirmed but the partner has not yet paid.\n"
                   " * The 'Active' status is used when the contract is "
                   "confirmed and until it's terminated.\n"
                   " * The 'Terminated' status is used when a contract is no "
                   "longer active.\n"
                   " * The 'Cancelled' status is used when a contract was "
                   "never paid.")),
        'is_active': fields.function(
            _active, string='Contract Active', type='boolean',
            store={
                'account.invoice': (_get_contract_from_invoice, ['state'], 50)
            },
            help="It indicates that the first invoice has been paid and the "
                 "contract was activated."),
        'fully_managed': fields.function(
            _is_fully_managed, type="boolean", store=True),
        # Field used for identifying gifts from sponsor (because of bad GP)
        'num_pol_ga': fields.integer(
            'Partner Contract Number', required=True
        ),
        'frequency': fields.related(
            'group_id', 'advance_billing', type="char", readonly=True,
            string=_('Frequency'), store=False),
        'end_reason': fields.selection(get_ending_reasons, _('End reason'),
                                       select=True),
        'end_date': fields.date(
            _('End date'), readonly=True,
            track_visibility="onchange"),
        'origin_id': fields.many2one('recurring.contract.origin', _("Origin"),
                                     required=True, ondelete='restrict',
                                     track_visibility='onchange'),
        'channel': fields.selection(_get_channels, string=_("Channel"),
                                    required=True, readonly=True,
                                    states={'draft': [('readonly', False)]}),
        'parent_id': fields.many2one(
            'recurring.contract', _('Previous sponsorship'),
            track_visibility='onchange'),
        'has_mandate': fields.function(
            _has_mandate, type='boolean', string='Has mandate'),
        'name': fields.function(_name_get, type='char'),
        'partner_id': fields.many2one(
            'res.partner', string=_('Partner'), required=True,
            readonly=False, states={'terminated': [('readonly', True)]},
            ondelete='restrict',
            track_visibility='onchange'),
    }

    _defaults = {
        'contract_line_ids': _get_standard_lines
    }

    ##########################
    #        CALLBACKS       #
    ##########################
    def name_get(self, cr, uid, ids, context=None):
        """ Gives a friendly name for a sponsorship """
        res = []
        for contract in self.browse(cr, uid, ids, context):
            name = contract.partner_id.ref
            if contract.child_id:
                name += ' - ' + contract.child_id.code
            elif contract.contract_line_ids:
                name += ' - ' + contract.contract_line_ids[0].product_id.name
            res.append((contract.id, name))
        return res

    def on_change_partner_id(self, cr, uid, ids, partner_id, context=None):
        ''' On partner change, we update the correspondent and
        set the new pol_number (for gift identification).'''
        res = super(recurring_contract, self).on_change_partner_id(
            cr, uid, ids, partner_id, context)
        num_contracts = self.search(
            cr, uid, [('partner_id', '=', partner_id)], context=context,
            count=True)
        # If contract created check state
        if ids:
            contract = self.browse(cr, uid, ids[0], context)
            # If state draft correspondant_id=parent_id
            if (contract.state == 'draft'):
                res['value'].update({
                    'correspondant_id': partner_id,
                })
        # Else correspondant_id=parent_id
        else:
            res['value'].update({
                'correspondant_id': partner_id,
            })
        res['value'].update({
            'num_pol_ga': num_contracts
        })
        return res

    def on_change_group_id(self, cr, uid, ids, group_id, context=None):
        """ Compute next invoice_date """
        res = dict()
        current_date = datetime.today()
        is_active = False
        if ids:
            contract = self.browse(cr, uid, ids[0], context)
            if contract.state not in (
                    'draft', 'mandate') and contract.next_invoice_date:
                is_active = True
                current_date = datetime.strptime(contract.next_invoice_date,
                                                 DF)
        if group_id:
            contract_group = self.pool.get('recurring.contract.group').browse(
                cr, uid, group_id, context)
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

        if current_date.day > 15 or (payment_term in ('LSV', 'Postfinance')
                                     and not is_active):
            next_invoice_date = next_invoice_date + relativedelta(months=+1)
        res['value'] = {'next_invoice_date': next_invoice_date.strftime(DF)}
        return res

    def contract_waiting(self, cr, uid, ids, context=None):
        for contract in self.browse(cr, uid, ids, {'lang': 'en_US'}):
            payment_term = contract.group_id.payment_term_id.name
            if 'LSV' in payment_term or 'Postfinance' in payment_term:
                # Recompute next_invoice_date
                today = datetime.today()
                next_invoice_date = datetime.strptime(
                    contract.next_invoice_date, DF).replace(month=today.month,
                                                            year=today.year)
                if today.day > 15 and next_invoice_date.day < 15:
                    next_invoice_date = next_invoice_date + relativedelta(
                        months=+1)
                contract.write({
                    'next_invoice_date': next_invoice_date.strftime(DF)})

            # Check that a child is selected for Sponsorship product
            if not contract.child_id:
                for line in contract.contract_line_ids:
                    if line.product_id.name == 'Sponsorship' or \
                            'LDP' in line.product_id.name:
                        raise orm.except_orm(
                            _("Please select a child"),
                            _("You should select a child if you "
                              "make a new sponsorship!"))

        self.write(cr, uid, ids, {'state': 'waiting'}, context)
        return True

    def contract_cancelled(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cancelled'}, context)
        # Remove the sponsor of the child
        for contract in self.browse(cr, uid, ids, context):
            if contract.child_id:
                contract.child_id.write({'sponsor_id': False})
        return True

    def contract_terminated(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'terminated'})

        ctx = {'lang': 'en_US'}
        category_obj = self.pool.get('res.partner.category')
        sponsor_cat_id = category_obj.search(
            cr, uid, [('name', '=', 'Sponsor')], context=ctx)[0]
        old_sponsor_cat_id = category_obj.search(
            cr, uid, [('name', '=', 'Old Sponsor')],
            context=ctx)[0]
        # Check if the sponsor has still active contracts
        for contract in self.browse(cr, uid, ids, context):
            con_ids = self.search(cr, uid, [
                ('partner_id', '=', contract.partner_id.id),
                ('state', '=', 'active')], context)
            if not con_ids:
                # Replace sponsor categoy by old sponsor category
                partner_categories = set(
                    [cat.id for cat in contract.partner_id.category_id])
                if sponsor_cat_id in partner_categories:
                    partner_categories.remove(sponsor_cat_id)
                partner_categories.add(old_sponsor_cat_id)
                # Standard way in Odoo to set one2many fields
                contract.partner_id.write({
                    'category_id': [(6, 0, list(partner_categories))]})
            # Remove the sponsor of the child
            if contract.child_id:
                contract.child_id.write({'sponsor_id': False})
        return True

    def contract_waiting_mandate(self, cr, uid, ids, context=None):
        for contract in self.browse(cr, uid, ids, context):
            # Check that a child is selected for Sponsorship product
            if not contract.child_id:
                for line in contract.contract_line_ids:
                    if line.product_id.name == 'Sponsorship' or \
                            'LDP' in line.product_id.name:
                        raise orm.except_orm(
                            _("Please select a child"),
                            _("You should select a child if you "
                              "make a new sponsorship!"))
        self.write(cr, uid, ids, {'state': 'mandate'}, context)
        return True

    def open_contract(self, cr, uid, ids, context=None):
        """ Used to bypass opening a contract in popup mode from
        res_partner view. """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contract',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': ids[0],
            'target': 'current',
        }

    def clean_invoices(self, cr, uid, ids, context=None, since_date=None):
        """ Take into consideration when the sponsor has paid in advance,
        so that we cancel/modify the paid invoices and let the user decide
        what to do with the payment.

        - The process bypasses the ORM by directly removing the invoice_lines
          concerning the cancelled contract. It also splits the sponsor's
          payment in order to be able to change the attribution of the amount
          that was destined to the cancelled contract.

        Note: direct access to database avoids to unreconcile and reconcile
              again invoices, which is a huge performance gain.
        """
        if not since_date:
            since_date = datetime.today().strftime(DF)

        # Find all paid invoice lines after the given date
        inv_line_obj = self.pool.get('account.invoice.line')
        inv_line_ids = inv_line_obj.search(
            cr, uid, [('contract_id', 'in', ids),
                      ('due_date', '>', since_date),
                      ('state', '=', 'paid')], context=context)

        # Invoice and move lines that need to be removed/updated
        to_remove_inv = set()
        to_update_inv = set()
        to_remove_mvl = list()
        to_remove_move = list()
        # Dictionary containing the total debit_lines in account 1050
        # for each invoice. These lines will be updated.
        # dict of format {move_line_id: debit_amount}
        to_update_mvl = dict()
        # Dictionary containing payment move_lines
        # dict of format {move_line_id: amount_removed}
        payment_mvl = dict()
        to_remove_pml = list()

        # Store data that is removed to pass it in sub_modules
        # Dictionary is in the following format :
        # {invoice_line_id: [invoice_id, child_code, product_name, amount]}
        invl_rm_data = dict()

        # 1. Determine which action has to be done for each invoice_line
        for inv_line in inv_line_obj.browse(cr, uid, inv_line_ids, context):
            invoice = inv_line.invoice_id
            to_update_inv.add(invoice.id)
            if inv_line.contract_id.child_id:
                # Store data before removal
                invl_rm_data[inv_line.id] = [
                    invoice.id, inv_line.contract_id.child_code,
                    inv_line.product_id.name, inv_line.price_subtotal]
            mvl_found = False
            for mvl in inv_line.invoice_id.move_id.line_id:
                if not mvl_found and \
                        mvl.product_id.id == inv_line.product_id.id \
                        and mvl.credit == inv_line.price_subtotal \
                        and mvl.id not in to_remove_mvl:
                    # Mark credit line to be removed
                    to_remove_mvl.append(mvl.id)
                    mvl_found = True
                elif mvl.debit > 0 and mvl.account_id.code == '1050':
                    # Remove amount of invoice_line from debit line
                    total_debit = to_update_mvl.get(mvl.id, mvl.debit)
                    to_update_mvl[mvl.id] = total_debit - \
                        inv_line.price_subtotal
                    if to_update_mvl[mvl.id] == 0:
                        # We deleted all invoice_lines and can delete the
                        # move associated with this invoice.
                        to_remove_mvl.append(mvl.id)
                        to_remove_move.append(mvl.move_id.id)
                    # Update payment lines related to this invoice
                    for pml in mvl.reconcile_id.line_id:
                        if pml.credit > inv_line.price_subtotal:
                            amount_deleted = payment_mvl.get(pml.id, 0.000)
                            payment_mvl[pml.id] = amount_deleted + \
                                inv_line.price_subtotal
                            if pml.credit == payment_mvl[pml.id]:
                                to_remove_pml.append(pml.id)
                            if pml.credit < payment_mvl[pml.id]:
                                self._clean_error()
                            # Update only one payment_line per invoice_line
                            break
            if not mvl_found:
                self._clean_error()
            # Mark empty invoice to be removed
            other_lines_ids = [invl.id for invl in invoice.invoice_line]
            remaining_lines_ids = [invl_id for invl_id in other_lines_ids
                                   if invl_id not in inv_line_ids]
            if not remaining_lines_ids:
                to_remove_inv.add(invoice.id)

        # 2. Manually remove invoice_lines, move_lines, empty invoices/moves
        if inv_line_ids:
            cr.execute(
                "DELETE FROM account_invoice_line WHERE id in ({0})"
                .format(','.join(str(id) for id in inv_line_ids)))
            if to_remove_inv:
                cr.execute(
                    "DELETE FROM account_invoice WHERE id in ({0})"
                    .format(','.join(str(id) for id in to_remove_inv)))
            cr.execute(
                "DELETE FROM account_move_line WHERE id in ({0})"
                .format(','.join(str(id) for id in to_remove_mvl)))
            if to_remove_move:
                cr.execute(
                    "DELETE FROM account_move WHERE id IN ({0})"
                    .format(','.join(str(id) for id in to_remove_move)))
            for mvl, amount in to_update_mvl.iteritems():
                cr.execute(
                    "UPDATE account_move_line SET debit={0:.3f} "
                    "WHERE id = {1:d}".format(amount, mvl))
            # Update the total field of invoices
            to_update_inv = to_update_inv - to_remove_inv
            self.pool.get('account.invoice').button_compute(
                cr, uid, list(to_update_inv), context=context, set_total=True)

            # 2.1. Split a payment so that the amount deleted is isolated
            #      in one move line that can be easily reconciled later.
            mvl_obj = self.pool.get('account.move.line')
            for pml_id, amount_deleted in payment_mvl.iteritems():
                cr.execute(
                    "UPDATE account_move_line SET credit=credit-{0:.3f} "
                    "WHERE id = {1:d}".format(
                        amount_deleted,
                        pml_id))
                mvl_obj.copy(
                    cr, uid, pml_id, default={
                        'reconcile_id': False,
                        'credit': amount_deleted}, context=context)
            if to_remove_pml:
                mvl_obj._remove_move_reconcile(cr, uid, to_remove_pml,
                                               context=context)
                cr.execute(
                    "DELETE FROM account_move_line WHERE id in ({0})"
                    .format(','.join(str(id) for id in to_remove_pml)))

            # 2.2 Call the hook for letting other modules handle the removal.
            self._on_invoice_line_removal(cr, uid, invl_rm_data, context)

        # 3. Clean open invoices
        super(recurring_contract, self).clean_invoices(
            cr, uid, ids, context, since_date)

        return True

    ################################
    #        PRIVATE METHODS       #
    ################################
    def _on_contract_active(self, cr, uid, ids, context=None):
        """ Hook for doing something when contract is activated.
        Update child to mark it has been sponsored, and update partner
        to add the 'Sponsor' category.
        """
        # Read data in english
        if context is None:
            context = {}
        ctx = context.copy()
        ctx['lang'] = 'en_US'
        wf_service = netsvc.LocalService('workflow')
        if not isinstance(ids, list):
            ids = [ids]
        sponsor_cat_id = self.pool.get('res.partner.category').search(
            cr, uid, [('name', '=', 'Sponsor')], context=ctx)[0]
        for contract in self.browse(cr, uid, ids, context=ctx):
            if contract.child_id:
                contract.child_id.write({'has_been_sponsored': True})
                partner_categories = set(
                    [cat.id for cat in contract.partner_id.category_id
                     if cat.name != 'Old Sponsor'])
                partner_categories.add(sponsor_cat_id)
                # Standard way in Odoo to set one2many fields
                contract.partner_id.write({
                    'category_id': [(6, 0, list(partner_categories))]})
            wf_service.trg_validate(
                uid, 'recurring.contract', contract.id,
                'contract_active', cr)
            logger.info("Contract " + str(contract.id) + " activated.")

    def _invoice_paid(self, cr, uid, invoice, context=None):
        """ Hook for doing something when an invoice is paid. """
        pass

    def _update_invoice_lines(self, cr, uid, contract, invoice_ids,
                              context=None):
        """Update invoice lines generated by a contract, when the contract
        was modified and corresponding invoices were cancelled.

        Parameters:
            - invoice_ids (list): ids of draft invoices to be
                                  updated and validated
        """
        invoice_obj = self.pool.get('account.invoice')
        inv_line_obj = self.pool.get('account.invoice.line')
        group_obj = self.pool.get('recurring.contract.group')
        for invoice in invoice_obj.browse(cr, uid, invoice_ids, context):
            # Update payment term and generate new invoice_lines
            invoice.write({
                'payment_term': contract.group_id.payment_term_id and
                contract.group_id.payment_term_id.id or False,
                'bvr_reference': contract.group_id.bvr_reference})
            old_lines_ids = [invl.id for invl in invoice.invoice_line
                             if invl.contract_id.id == contract.id]
            inv_line_obj.unlink(cr, uid, old_lines_ids)
            context['no_next_date_update'] = True
            group_obj._generate_invoice_lines(cr, uid, contract,
                                              invoice.id, context)
            del(context['no_next_date_update'])

    def _on_invoice_line_removal(self, cr, uid, invoice_line, context=None):
        # Hook for doing something before invoice_line deletion
        pass

    def _clean_error(self):
        raise orm.except_orm(
            _('Cancel Invoice Error'),
            _('The sponsor has already paid in advance for this '
              'sponsorship, but the system was unable to automatically '
              'cancel the invoices. Please refer to an accountant for '
              'changing the attribution of his payment before cancelling '
              'the sponsorship.'))

    def _reset_open_invoices(self, cr, uid, ids, context=None):
        """Clean the open invoices in order to generate new invoices.
        This can be useful if contract was updated when active."""
        invoices_canceled = super(recurring_contract, self).clean_invoices(
            cr, uid, ids, context)
        if invoices_canceled:
            invoice_obj = self.pool.get('account.invoice')
            since_date = datetime.today().replace(day=1).strftime(DF)
            inv_update_ids = set()
            for contract in self.browse(cr, uid, ids, context):
                # If some invoices are left cancelled, we update them
                # with new contract information and validate them
                cancel_ids = invoice_obj.search(cr, uid, [
                    ('state', '=', 'cancel'),
                    ('id', 'in', list(invoices_canceled)),
                    ('date_invoice', '>=', since_date)], context=context)
                if cancel_ids:
                    inv_update_ids.update(cancel_ids)
                    invoice_obj.action_cancel_draft(cr, uid, cancel_ids)
                    self._update_invoice_lines(cr, uid, contract, cancel_ids,
                                               context)
                # If no invoices are left in cancel state, we rewind
                # the next_invoice_date for the contract to generate again
                else:
                    next_invoice_date = datetime.strptime(
                        contract.next_invoice_date, DF)
                    next_invoice_date = next_invoice_date + relativedelta(
                        months=-len(invoices_canceled))
                    super(recurring_contract, self).write(
                        cr, uid, contract.id, {
                            'next_invoice_date': next_invoice_date.strftime(
                                DF)}, context)
                    invoicer_id = contract.group_id.generate_invoices()
                    invoicer = self.pool.get('recurring.invoicer').browse(
                        cr, uid, invoicer_id, context)
                    if invoicer.invoice_ids:
                        invoicer.validate_invoices()
                    else:
                        invoicer.unlink()
            # Validate again modified invoices
            if inv_update_ids:
                wf_service = netsvc.LocalService('workflow')
                for invoice_id in inv_update_ids:
                    wf_service.trg_validate(
                        uid, 'account.invoice', invoice_id,
                        'invoice_open', cr)
        return True

    def _on_change_next_invoice_date(self, cr, uid, ids, next_invoice_date,
                                     context=None):
        """Prevent to change next_invoice_date in the past
        for active contract.
        """
        for contract in self.browse(cr, uid, ids, context):
            if contract.state not in ('draft', 'mandate') \
                    and next_invoice_date < contract.next_invoice_date:
                raise orm.except_orm(
                    _('Warning'),
                    _('You cannot rewind the next invoice date.'))

    def _on_change_child_id(self, cr, uid, ids, child_id, partner_id=None,
                            context=None):
        """Link/unlink child to sponsor
        """
        for contract in self.browse(cr, uid, ids, context):
            if contract.child_id and contract.child_id != child_id:
                # Free the previously selected child
                contract.child_id.write({'sponsor_id': False})
            if child_id:
                # Mark the selected child as sponsored
                self.pool.get('compassion.child').write(
                    cr, uid, child_id, {
                        'sponsor_id': partner_id or contract.partner_id.id},
                    context)

    def _on_change_group_id(self, cr, uid, ids, group_id, context=None):
        """ Change state of contract if payment is changed to/from LSV or DD.
        """
        wf_service = netsvc.LocalService('workflow')
        group = self.pool.get('recurring.contract.group').browse(
            cr, uid, group_id, context)
        payment_name = group.payment_term_id.name
        if 'LSV' in payment_name or 'Postfinance' in payment_name:
            for id in ids:
                wf_service.trg_validate(
                    uid, 'recurring.contract', id,
                    'will_pay_by_lsv_dd', cr)
        else:
            # Check if old payment_term was LSV or DD
            for contract in self.browse(cr, uid, ids, context):
                payment_name = contract.group_id.payment_term_id.name
                if 'LSV' in payment_name or 'Postfinance' in payment_name:
                    wf_service.trg_validate(
                        uid, 'recurring.contract', contract.id,
                        'mandate_validated', cr)

    def _on_contract_lines_changed(self, cr, uid, ids, context=None):
        """Update related invoices to reflect the changes to the contract.
        """
        invoice_obj = self.pool.get('account.invoice')
        inv_line_obj = self.pool.get('account.invoice.line')
        # Find all unpaid invoice lines after the given date
        since_date = datetime.today().replace(day=1).strftime(DF)
        inv_line_ids = inv_line_obj.search(
            cr, uid, [('contract_id', 'in', ids),
                      ('due_date', '>=', since_date),
                      ('state', 'not in', ('paid', 'cancel'))],
            context=context)
        con_ids = set()
        inv_ids = set()
        for inv_line in inv_line_obj.browse(cr, uid, inv_line_ids, context):
            invoice = inv_line.invoice_id
            if invoice.id not in inv_ids or \
                    inv_line.contract_id.id not in con_ids:
                con_ids.add(inv_line.contract_id.id)
                inv_ids.add(invoice.id)
                invoice_obj.action_cancel(cr, uid, [invoice.id], context)
                invoice_obj.action_cancel_draft(cr, uid, [invoice.id])
                self._update_invoice_lines(cr, uid, inv_line.contract_id,
                                           [invoice.id], context)
        wf_service = netsvc.LocalService('workflow')
        for invoice in invoice_obj.browse(cr, uid, list(inv_ids), context):
            wf_service.trg_validate(
                uid, 'account.invoice', invoice.id, 'invoice_open', cr)

    def _on_group_id_changed(self, cr, uid, ids, context=None):
        """Remove lines of open invoices and generate them again
        """
        self._reset_open_invoices(cr, uid, ids, context)
        for contract in self.browse(cr, uid, ids, context=context):
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

    ################################
    #        PUBLIC METHODS        #
    ################################
    def create(self, cr, uid, vals, context=None):
        """Link child to sponsor.
        """
        child_id = vals.get('child_id')
        if child_id:
            self.pool.get('compassion.child').write(
                cr, uid, child_id, {
                    'sponsor_id': vals['partner_id']}, context)
        return super(recurring_contract, self).create(cr, uid, vals, context)

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = dict()
        num_pol_ga = self.browse(cr, uid, id, context=context).num_pol_ga
        default.update({
            'child_id': False,
            'activation_date': False,
            'is_active': False,
            'num_pol_ga': num_pol_ga + 1,
        })
        return super(recurring_contract, self).copy(cr, uid, id, default,
                                                    context)

    def unlink(self, cr, uid, ids, context=None):
        for contract in self.browse(cr, uid, ids, context):
            # We can only delete draft contracts.
            if contract.state != 'draft':
                raise orm.except_orm(_('Warning'),
                                     _('You cannot delete a contract that is '
                                       'still active. Terminate it first.'))
            else:
                if contract.child_id:
                    contract.child_id.write({'sponsor_id': False})

        super(recurring_contract, self).unlink(cr, uid, ids,
                                               context=context)
        return

    def write(self, cr, uid, ids, vals, context=None):
        """ Perform various checks when a contract is modified. """
        if 'next_invoice_date' in vals:
            self._on_change_next_invoice_date(
                cr, uid, ids, vals['next_invoice_date'], context)
        if 'child_id' in vals:
            self._on_change_child_id(cr, uid, ids, vals['child_id'],
                                     vals.get('partner_id'), context)
        if 'group_id' in vals:
            self._on_change_group_id(cr, uid, ids, vals['group_id'], context)

        # Write the changes
        res = super(recurring_contract, self).write(cr, uid, ids, vals,
                                                    context=context)

        if 'contract_line_ids' in vals:
            self._on_contract_lines_changed(cr, uid, ids, context)
        if 'group_id' in vals or 'partner_id' in vals:
            self._on_group_id_changed(cr, uid, ids, context)

        return res

    ##############################
    #      CALLBACKS FOR GP      #
    ##############################
    def force_validation(self, cr, uid, contract_id, context=None):
        """ Used to transition draft sponsorships in waiting state
        when exported from GP. """
        wf_service = netsvc.LocalService('workflow')
        logger.info("Contract " + str(contract_id) + " validated.")
        wf_service.trg_validate(uid, 'recurring.contract', contract_id,
                                'contract_validated', cr)
        return True

    def force_activation(self, cr, uid, contract_id, context=None):
        """ Used to transition draft sponsorships in active state
        when exported from GP. """
        self.force_validation(cr, uid, contract_id, context)
        self._on_contract_active(cr, uid, [contract_id], context)
        return True

    def force_termination(self, cr, uid, contract_id, end_state, end_reason,
                          child_state, child_exit_code, end_date,
                          transfer_country_code, context=None):
        """ Used to delete the workflow of terminated or cancelled
        sponsorships when exported from GP. """
        # Write sponsorship end reason
        sponsor_reasons = [reason[0] for reason in self.get_ending_reasons(
            cr, uid, context)]
        end_reason = str(end_reason)
        if end_reason not in sponsor_reasons:
            end_reason = '1'
        vals = {'state': end_state,
                'end_reason': str(end_reason),
                'end_date': end_date or False}
        self.write(cr, uid, contract_id, vals, context)

        # Mark child as departed
        contract = self.browse(cr, uid, contract_id, context)
        child_vals = {}
        if child_state == 'F' and contract.child_id:
            child_vals['state'] = 'F'
            child_exit_code = str(child_exit_code)
            exit_reasons = [reason[0] for reason in self.pool.get(
                'compassion.child').get_gp_exit_reasons(cr, uid, context)]
            if child_exit_code in exit_reasons:
                child_vals['gp_exit_reason'] = str(child_exit_code)
            else:
                country_id = self.pool.get('res.country').search(
                    cr, uid, [('code', '=', transfer_country_code)],
                    context=context)
                if country_id:
                    country_id = country_id[0]
                    child_vals['transfer_country_id'] = country_id
        if contract.child_id:
            child_vals['sponsor_id'] = False
            contract.child_id.write(child_vals)

        # Delete workflow for this contract
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_delete(uid, 'recurring.contract', contract_id, cr)
        logger.info("Contract " + str(contract_id) + " terminated.")
        return True


# just to modify access rights...
class recurring_invoicer(orm.Model):
    _inherit = 'recurring.invoicer'
    _name = 'recurring.invoicer'


class account_invoice(orm.Model):
    _inherit = 'account.invoice'
    _name = 'account.invoice'


class contract_line(orm.Model):
    _inherit = 'recurring.contract.line'


class account_move(orm.Model):
    _inherit = 'account.move'


class account_move_line(orm.Model):
    _inherit = 'account.move.line'


class payment_line(orm.Model):
    _inherit = 'payment.line'


class account_journal(orm.Model):
    _inherit = 'account.journal'


class account_asset_depreciation_line(orm.Model):
    _inherit = 'account.asset.depreciation.line'


class account_analytic_plan_instance(orm.Model):
    _inherit = 'account.analytic.plan.instance'


class account_analytic_plan_instance_line(orm.Model):
    _inherit = 'account.analytic.plan.instance.line'


class account_period(orm.Model):
    _inherit = 'account.period'


class account_account_type(orm.Model):
    _inherit = 'account.account.type'
