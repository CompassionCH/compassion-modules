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

from openerp.osv import orm
from openerp import netsvc
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

from datetime import datetime
from dateutil.relativedelta import relativedelta


import logging


logger = logging.getLogger(__name__)


class sponsorship_contract(orm.Model):
    _inherit = 'recurring.contract'

    def _get_sponsorship_standard_lines(self, cr, uid, context=None):
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

    def _get_standard_lines(self, cr, uid, context=None):
        if context['default_type'] == 'S':
            return self._get_sponsorship_standard_lines(cr, uid, context)
        return []

    _defaults = {
        'contract_line_ids': _get_standard_lines
    }

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

    def clean_invoices(
            self, cr, uid, ids, context=None, since_date=None, to_date=None):
        if type == 'S':
            self.clean_invoices_paid(
                cr, uid, ids, context, since_date, to_date)

        return super(sponsorship_contract, self).clean_invoices(
            cr, uid, ids, context, since_date, to_date)

    def clean_invoices_paid(self, cr, uid, ids, context=None, since_date=None,
                            to_date=None):
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
        # Find all paid invoice lines after the given date
        inv_line_obj = self.pool.get('account.invoice.line')
        invl_search = self._filter_clean_invoices(cr, uid, ids, since_date,
                                                  to_date, context)
        inv_line_ids = inv_line_obj.search(cr, uid, invl_search,
                                           context=context)

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
        #    and reconcile refs that are no longer valid
        if inv_line_ids:
            # 2.1 Call the hook for letting other modules handle the removal.
            self._on_invoice_line_removal(cr, uid, invl_rm_data, context)

            cr.execute(
                "DELETE FROM account_invoice_line WHERE id in ({0})"
                .format(','.join(str(id) for id in inv_line_ids)))
            if to_remove_inv:
                cr.execute(
                    "DELETE FROM account_invoice WHERE id in ({0})"
                    .format(','.join(str(id) for id in to_remove_inv)))
            # Remove move lines and invalid reconcile refs
            mvl_ids_string = ','.join(str(id) for id in to_remove_mvl)
            cr.execute(
                "DELETE FROM account_move_line WHERE id in ({0});"
                "DELETE FROM account_move_reconcile rec WHERE ("
                "   SELECT count(*) FROM account_move_line "
                "   WHERE reconcile_id = rec.id) < 2;"
                .format(mvl_ids_string))
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

            # 2.2. Split a payment so that the amount deleted is isolated
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

        # 3. Clean open invoices
        super(sponsorship_contract, self).clean_invoices(
            cr, uid, ids, context, since_date, to_date)

        return True

    def _invoice_paid(self, cr, uid, invoice, context=None):
        """ Prevent to reconcile invoices for fund-suspended projects. """
        if invoice.payment_ids:
            for invl in invoice.invoice_line:
                if invl.contract_id and invl.contract_id.child_id:
                    payment_allowed = True
                    project = invl.contract_id.child_id.project_id
                    if invl.product_id.type == 'G':
                        payment_allowed = project.disburse_gifts or \
                            invl.due_date < project.status_date
                    else:
                        payment_allowed = project.disburse_funds or \
                            invl.due_date < project.status_date
                    if not payment_allowed:
                        raise orm.except_orm(
                            _("Reconcile error"),
                            _("The project %s is fund-suspended. You cannot "
                              "reconcile this invoice.") % project.code)

    def suspend_contract(self, cr, uid, ids, context=None, date_start=None,
                         date_end=None):
        """Cancels the number of invoices specified starting
        from a given date. This is useful to suspend a contract for a given
        period."""
        # By default, we suspend the contract for 3 months starting from today
        if not date_start:
            date_start = datetime.today()
        if not date_end:
            date_end = date_start + relativedelta(months=3)

        # Cancel invoices in the period of suspension
        self.clean_invoices(cr, uid, ids, context, date_start.strftime(DF),
                            date_end.strftime(DF))

        for contract in self.browse(cr, uid, ids, context):
            # Advance next invoice date after end of suspension
            next_inv_date = datetime.strptime(contract.next_invoice_date, DF)
            months = relativedelta(date_end, date_start).months
            month_diff = relativedelta(date_end, next_inv_date).months
            if month_diff > 0:
                # If sponsorship is late, don't advance it too much
                if month_diff > months:
                    month_diff = months
                new_date = next_inv_date + relativedelta(months=month_diff)
                contract.write({'next_invoice_date': new_date.strftime(DF)})

            # Add a note in the contract and in the partner.
            project_code = contract.child_id.project_id.code
            self.pool.get('mail.thread').message_post(
                cr, uid, contract.id,
                "The project {0} was suspended and funds are retained <b>"
                "until {1}</b>.<br/>Invoices due in the suspension period "
                "are automatically cancelled.".format(
                    project_code, date_end.strftime("%B %Y")),
                "Project Suspended", 'comment',
                context={'thread_model': 'recurring.contract'})
            self.pool.get('mail.thread').message_post(
                cr, uid, contract.partner_id.id,
                "The project {0} was suspended and funds are retained "
                "for child {2} <b>"
                "until {1}</b>.<br/>Invoices due in the suspension period "
                "are automatically cancelled.".format(
                    project_code, date_end.strftime("%B %Y"),
                    contract.child_id.code),
                "Project Suspended", 'comment',
                context={'thread_model': 'res.partner'})

        return True

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

    def contract_waiting_mandate(self, cr, uid, ids, context=None):
        for contract in self.browse(cr, uid, ids, context):
            # Check that a child is selected for Sponsorship product
            if not contract.child_id:
                raise orm.except_orm(
                    _("Please select a child"),
                    _("You should select a child if you "
                      "make a new sponsorship!"))
        return super(sponsorship_contract, self).contract_waiting_mandate(
            cr, uid, ids, context)

    def contract_waiting(self, cr, uid, ids, context=None):
        for contract in self.browse(cr, uid, ids, {'lang': 'en_US'}):
            # Check that a child is selected for Sponsorship product
            if not contract.child_id:
                raise orm.except_orm(
                    _("Please select a child"),
                    _("You should select a child if you "
                      "make a new sponsorship!"))

        return super(sponsorship_contract, self).contract_waiting(
            cr, uid, ids, context)

    def on_change_partner_id(self, cr, uid, ids, partner_id, context=None):
        res = super(sponsorship_contract, self).on_change_partner_id(
            cr, uid, ids, partner_id, context)

        # Check if group_id is valid
        if 'group_id' in res['value']:
            if not self._is_a_valid_group(
                    cr, uid, res['value']['group_id'], context):
                del res['value']['group_id']
        return res

    def _is_a_valid_group(self, cr, uid, group_id, context=None):
        group_obj = self.pool.get('recurring.contract.group')
        group = group_obj.browse(cr, uid, group_id, context)

        if not group.contains_sponsorship or group.recurring_value != 1:
            return False
        return True

    def create(self, cr, uid, vals, context):
        ''' Check if group is valid for these contracts on create '''
        if 'group_id' in vals:
            if context['default_type'] == 'S':
                group_id = vals['group_id']
                if not self._is_a_valid_group(cr, uid, group_id, context):
                    raise orm.except_orm(
                        _('Please select a valid payment option'),
                        _('You should select payment option with'
                          '"1 month" as recurring value')
                    )
        return super(sponsorship_contract, self).create(
            cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context):
        ''' Check if group is valid for these contracts on write '''
        for contract in self.browse(cr, uid, ids, context):
            if 'group_id' in vals:
                group_id = vals['group_id']
                if contract.type == 'S':
                    if not self._is_a_valid_group(cr, uid, group_id, context):
                        raise orm.except_orm(
                            _('Please select a valid payment option'),
                            _('You should select payment option with'
                              '"1 month" as recurring value')
                        )

        return super(sponsorship_contract, self).write(
            cr, uid, ids, vals, context)
