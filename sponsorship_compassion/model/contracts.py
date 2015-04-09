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

from .product import GIFT_TYPES

import logging

logger = logging.getLogger(__name__)


class recurring_contract(orm.Model):
    _inherit = "recurring.contract"
    _name = 'sponsorship.contract'

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
        
    def _invoice_paid(self, cr, uid, invoice, context=None):
        """ Prevent to reconcile invoices for fund-suspended projects. """
        if invoice.payment_ids:
            for invl in invoice.invoice_line:
                if invl.contract_id and invl.contract_id.child_id:
                    payment_allowed = True
                    project = invl.contract_id.child_id.project_id
                    if invl.product_id.name in GIFT_TYPES:
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
        return super(Sponsorship_contract).contract_waiting_mandate(cr, uid, ids, context)
        
    def contract_waiting(self, cr, uid, ids, context=None):
        for contract in self.browse(cr, uid, ids, {'lang': 'en_US'}):
            # Check that a child is selected for Sponsorship product
            if not contract.child_id:
                raise orm.except_orm(
                    _("Please select a child"),
                    _("You should select a child if you "
                      "make a new sponsorship!"))

        return super(Sponsorship_contract).contract_waiting(cr, uid, ids, context)
    
        