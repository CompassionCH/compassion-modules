# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
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

from lxml import etree

from .product import GIFT_CATEGORY, SPONSORSHIP_CATEGORY, FUND_CATEGORY

import logging


logger = logging.getLogger(__name__)


class sponsorship_line(orm.Model):
    _inherit = 'recurring.contract.line'

    _columns = {
        'sponsorship_id': fields.many2one(
            'recurring.contract', _('Sponsorship'))
    }

    def fields_view_get(self, cr, user, view_id=None, view_type='tree',
                        context=None, toolbar=False, submenu=False):
        """ Change product domain depending on contract type. """
        res = super(sponsorship_line, self).fields_view_get(
            cr, user, view_id, view_type, context, toolbar, submenu)

        if view_type == 'tree':
            type = context.get('default_type', 'O')
            if 'S' in type:
                res['fields']['product_id']['domain'] = [
                    ('categ_name', 'in', [SPONSORSHIP_CATEGORY,
                                          FUND_CATEGORY])]
                # Remove field sponsorship_id for sponsorship contracts
                doc = etree.XML(res['arch'])
                for node in doc.xpath("//field[@name='sponsorship_id']"):
                    node.getparent().remove(node)
                res['arch'] = etree.tostring(doc)
                del(res['fields']['sponsorship_id'])
            else:
                res['fields']['product_id']['domain'] = [
                    ('categ_name', '!=', SPONSORSHIP_CATEGORY)]

        return res


class sponsorship_contract(orm.Model):
    _inherit = 'recurring.contract'

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def get_ending_reasons(self, cr, uid, context=None):
        res = super(sponsorship_contract, self).get_ending_reasons(
            cr, uid, context)

        if 'active_id' in context and \
                context.get('active_model') == self._name:
            type = self.browse(cr, uid, context['active_id'], context).type
        else:
            type = context.get('default_type', 'O')

        if 'S' in type:
            res.extend([
                ('1', _("Depart of child")),
                ('10', _("Subreject")),
                ('11', _("Exchange of sponsor"))
                ])
            res.sort(key=lambda tup: int(float(tup[0])))  # Sort res
        return res

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
        if 'S' in context.get('default_type', 'O'):
            return self._get_sponsorship_standard_lines(cr, uid, context)
        return []

    def _is_fully_managed(self, cr, uid, ids, field_name, arg, context):
        """Tells if the correspondent and the payer is the same person."""
        res = dict()
        for contract in self.browse(cr, uid, ids, context=context):
            res[contract.id] = (contract.partner_id ==
                                contract.correspondant_id)
        return res

    def _get_type(self, cr, uid, context=None):
        res = super(sponsorship_contract, self)._get_type(cr, uid, context)
        res.extend([
            ('G', _('Child Gift')),
            ('S', _('Sponsorship')),
            ('SC', _('Correspondence'))])
        return res

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    _columns = {
        'correspondant_id': fields.many2one(
            'res.partner', _('Correspondant'), required=True, readonly=True,
            states={'draft': [('readonly', False)],
                    'waiting': [('readonly', False)],
                    'mandate': [('readonly', False)]},
            track_visibility='onchange'),
        'partner_codega': fields.related(
            'correspondant_id', 'ref', string=_('Partner ref'), readonly=True,
            type='char'),
        'fully_managed': fields.function(
            _is_fully_managed, type="boolean", store={
                'recurring.contract': (
                    lambda self, cr, uid, ids, c=None: ids,
                    ['partner_id', 'correspondant_id'], 10)
            }),
        'birthday_invoice': fields.float(_("Annual birthday gift"), help=_(
            "Set the amount to enable automatic invoice creation each year "
            "for a birthday gift. The invoice is set two months before "
            "child's birthday."), track_visibility='onchange'),
    }

    _defaults = {
        'contract_line_ids': _get_standard_lines
    }

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    def create(self, cr, uid, vals, context):
        """ Perform various checks on contract creations
        """
        child_id = vals.get('child_id')
        if 'S' in vals.get('type', '') and child_id:
            self.pool.get('compassion.child').write(
                cr, uid, child_id, {
                    'sponsor_id': vals['partner_id']}, context)

        if 'group_id' in vals:
            if 'S' in context.get('default_type', 'O'):
                group_id = vals['group_id']
                if not self._is_a_valid_group(cr, uid, group_id, context):
                    raise orm.except_orm(
                        _('Please select a valid payment option'),
                        _('You should select payment option with '
                          '"1 month" as recurring value')
                    )
        if 'contract_line_ids' in vals:
            self._has_valid_contract_lines(
                cr, uid, vals['contract_line_ids'],
                vals.get('type', context.get('default_type')), context)

        return super(sponsorship_contract, self).create(
            cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context):
        """ Perform various checks on contract modification """
        if not isinstance(ids, list):
            ids = [ids]
        for contract in self.browse(cr, uid, ids, context):
            if 'child_id' in vals:
                self._on_change_child_id(cr, uid, ids, vals, context)
            if 'group_id' in vals:
                group_id = vals['group_id']
                if 'S' in contract.type:
                    if not self._is_a_valid_group(cr, uid, group_id, context):
                        raise orm.except_orm(
                            _('Please select a valid payment option'),
                            _('You should select payment option with'
                              '"1 month" as recurring value')
                        )
            if 'contract_line_ids' in vals:
                self._has_valid_contract_lines(
                    cr, uid, vals['contract_line_ids'],
                    vals.get('type', contract.type), context)

        return super(sponsorship_contract, self).write(
            cr, uid, ids, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        for contract in self.browse(cr, uid, ids, context):
            if 'S' in contract.type and contract.child_id:
                child_sponsor_id = contract.child_id.sponsor_id and \
                    contract.child_id.sponsor_id.id
                if child_sponsor_id == contract.correspondant_id.id:
                    contract.child_id.write({'sponsor_id': False})
        res = super(sponsorship_contract, self).unlink(cr, uid, ids, context)
        return res

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def clean_invoices(
            self, cr, uid, ids, context=None, since_date=None, to_date=None,
            keep_lines=None, clean_invoices_paid=True):
        """ Take into consideration when the sponsor has paid in advance,
        so that we cancel/modify the paid invoices and let the user decide
        what to do with the payment.
        """
        sponsorship_ids = self.search(cr, uid, [
            ('id', 'in', ids),
            ('type', 'like', 'S')], context=context)
        if clean_invoices_paid:
            self.clean_invoices_paid(
                cr, uid, sponsorship_ids, context, since_date, to_date,
                keep_lines=keep_lines)

        return super(sponsorship_contract, self).clean_invoices(
            cr, uid, ids, context, since_date, to_date, keep_lines)

    def clean_invoices_paid(self, cr, uid, ids, context=None, since_date=None,
                            to_date=None, gifts=False, keep_lines=None):
        """ Removes or cancel paid invoices in the given period.

        - The process bypasses the ORM by directly removing the invoice_lines
          concerning the given contracts. It also splits the sponsor's
          payment in order to be able to change the attribution of the amount
          that was destined to the cancelled contract.

        Note: direct access to database avoids to unreconcile and reconcile
              again invoices, which is a huge performance gain.
        """
        # Find all paid invoice lines after the given date
        inv_line_obj = self.pool.get('account.invoice.line')
        invl_search = self._filter_clean_invoices(cr, uid, ids, since_date,
                                                  to_date, gifts, context)
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
        # Dictionary containing payment move_lines that need to be splitted
        # dict of format {move_line_id: amount_removed}
        split_payment_mvl = dict()
        unrec_pml = list()

        # Store data that is removed to pass it in sub_modules
        # Dictionary is in the following format :
        # {invoice_line_id: [invoice_id, child_code, product_name, amount]}
        invl_rm_data = dict()

        # 1. Determine which action has to be done for each invoice_line
        self._how_to_clean_invl(
            cr, uid, inv_line_ids, to_remove_inv, to_update_inv,
            to_remove_mvl, to_remove_move, to_update_mvl, split_payment_mvl,
            unrec_pml, invl_rm_data, context)

        # 2. Manually remove invoice_lines, move_lines, empty invoices/moves
        #    and reconcile refs that are no longer valid
        if inv_line_ids:
            # Call the hook for letting other modules handle the removal.
            self._on_invoice_line_removal(cr, uid, invl_rm_data, context)

            self._clean_paid_invoice_lines(cr, uid, list(to_remove_inv),
                                           list(to_update_inv), inv_line_ids,
                                           keep_lines, context)

            self._clean_move_lines(cr, to_remove_mvl, to_remove_move,
                                   to_update_mvl)

            # Update the total field of invoices
            self.pool.get('account.invoice').button_compute(
                cr, uid, list(to_update_inv), context=context, set_total=True)

            # 2.2. Split or unreconcile payment so that the amount deleted is
            #      isolated.
            self._unrec_split_payment(cr, uid, split_payment_mvl, unrec_pml,
                                      context)

        return True

    def suspend_contract(self, cr, uid, ids, context=None):
        """
        If ir.config.parameter is set : change sponsorship invoices with
        a fund donation set in the config.
        Otherwise, Cancel the number of invoices specified starting
        from a given date. This is useful to suspend a contract for a given
        period."""
        date_start = datetime.today().strftime(DF)

        config_obj = self.pool.get('ir.config_parameter')
        suspend_config_id = config_obj.search(cr, uid, [
            ('key', '=', 'sponsorship_compassion.suspend_product_id')],
            context=context)

        # Cancel invoices in the period of suspension
        self.clean_invoices(cr, uid, ids, context, date_start,
                            keep_lines=_('Center suspended'))

        for contract in self.browse(cr, uid, ids, context):
            # Add a note in the contract and in the partner.
            project_code = contract.child_id.project_id.code
            self.pool.get('mail.thread').message_post(
                cr, uid, contract.id,
                "The project {0} was suspended and funds are retained."
                "<br/>Invoices due in the suspension period "
                "are automatically cancelled.".format(
                    project_code),
                "Project Suspended", 'comment',
                context={'thread_model': self._name})
            self.pool.get('mail.thread').message_post(
                cr, uid, contract.partner_id.id,
                "The project {0} was suspended and funds are retained "
                "for child {1}. <b>"
                "<br/>Invoices due in the suspension period "
                "are automatically cancelled.".format(
                    project_code, contract.child_id.code),
                "Project Suspended", 'comment',
                context={'thread_model': 'res.partner'})

        # Change invoices if config tells to do so.
        if suspend_config_id:
            product_id = int(config_obj.browse(cr, uid, suspend_config_id[0],
                                               context).value)
            self._suspend_change_invoices(cr, uid, ids, date_start,
                                          product_id, context)

        return True

    def _suspend_change_invoices(self, cr, uid, ids, since_date,
                                 product_id, context=None):
        """ Change cancelled sponsorship invoices and put them for given
        product. Re-open invoices. """
        invl_obj = self.pool.get('account.invoice.line')
        cancel_invl_ids = invl_obj.search(cr, uid, [
            ('contract_id', 'in', ids),
            ('state', '=', 'cancel'),
            ('product_id.categ_name', '=', SPONSORSHIP_CATEGORY),
            ('due_date', '>=', since_date)], context=context)
        invoice_ids = set()
        for invl in invl_obj.browse(cr, uid, cancel_invl_ids,
                                    {'lang': 'en_US'}):
            invoice_ids.add(invl.invoice_id.id)
        invoice_ids = list(invoice_ids)
        self.pool.get('account.invoice').action_cancel_draft(
            cr, uid, invoice_ids)
        vals = self.get_suspend_invl_data(cr, uid, product_id, context)
        invl_obj.write(cr, uid, cancel_invl_ids, vals, context)
        wf_service = netsvc.LocalService('workflow')
        for invoice_id in invoice_ids:
            wf_service.trg_validate(uid, 'account.invoice',
                                    invoice_id, 'invoice_open', cr)

    def get_suspend_invl_data(self, cr, uid, product_id, context=None):
        """ Returns invoice_line data for a given product when center
        is suspended. """
        product = self.pool.get('product.product').browse(cr, uid, product_id,
                                                          context)
        vals = {
            'product_id': product_id,
            'account_id': product.property_account_income.id,
            'name': 'Replacement of sponsorship (fund-suspended)'}
        rec = self.pool.get('account.analytic.default').account_get(
            cr, uid, product_id, context=context)
        if rec and rec.analytic_id:
            vals['account_analytic_id'] = rec.analytic_id.id

        return vals

    def reactivate_contract(self, cr, uid, ids, context):
        """ When project is reactivated, we re-open cancelled invoices,
        or we change open invoices if fund is set to replace sponsorship
        product. We also change attribution of invoices paid in advance.
        """
        date_start = datetime.today().strftime(DF)
        config_obj = self.pool.get('ir.config_parameter')
        wf_service = netsvc.LocalService('workflow')
        suspend_config_id = config_obj.search(cr, uid, [
            ('key', '=', 'sponsorship_compassion.suspend_product_id')],
            context=context)
        invl_obj = self.pool.get('account.invoice.line')
        invoice_obj = self.pool.get('account.invoice')
        product_obj = self.pool.get('product.product')
        sponsorship_product = product_obj.browse(cr, uid, product_obj.search(
            cr, uid, [('name', '=', SPONSORSHIP_CATEGORY)])
            [0], context)
        contract_ids = set()
        if suspend_config_id:
            # Revert future invoices with sponsorship product
            susp_product_id = int(config_obj.browse(
                cr, uid, suspend_config_id[0], context).value)
            invl_ids = invl_obj.search(cr, uid, [
                ('contract_id', 'in', ids),
                ('product_id', '=', susp_product_id),
                ('state', 'in', ['open', 'paid']),
                ('due_date', '>=', date_start)], context=context)
            invl_data = {
                'product_id': sponsorship_product.id,
                'account_id': sponsorship_product.property_account_income.id,
                'name': sponsorship_product.name
            }
            rec = self.pool.get('account.analytic.default').account_get(
                cr, uid, sponsorship_product.id, context=context)
            if rec and rec.analytic_id:
                invl_data['account_analytic_id'] = rec.analytic_id.id
            invl_obj.write(cr, uid, invl_ids, invl_data, context)

            inv_ids = set()
            mvl_paid_ids = set()
            for invoice_line in invl_obj.browse(cr, uid, invl_ids, context):
                invoice = invoice_line.invoice_id
                inv_ids.add(invoice.id)
                contract_ids.add(invoice_line.contract_id.id)
                if invoice.state == 'paid':
                    mvl_paid_ids |= set([
                        l.id for l in
                        invoice.payment_ids[0].reconcile_id.line_id])

            # Unreconcile paid invoices
            self.pool.get('account.move.line')._remove_move_reconcile(
                cr, uid, list(mvl_paid_ids), context=context)
            # Cancel and confirm again invoices to update move lines
            inv_ids = list(inv_ids)
            invoice_obj.action_cancel(cr, uid, inv_ids)
            invoice_obj.action_cancel_draft(cr, uid, inv_ids)
            for inv_id in inv_ids:
                wf_service.trg_validate(
                    uid, 'account.invoice', inv_id, 'invoice_open', cr)
        else:
            # Open again cancelled invoices
            invl_ids = invl_obj.search(cr, uid, [
                ('contract_id', 'in', ids),
                ('product_id', '=', sponsorship_product.id),
                ('state', '=', 'cancel'),
                ('due_date', '>=', date_start)], context=context)
            for invoice_line in invl_obj.browse(cr, uid, invl_ids, context):
                invoice = invoice_line.invoice_id
                contract_ids.add(invoice_line.contract_id.id)
                if invoice.state == 'cancel':
                    invoice_obj.action_cancel_draft(cr, uid, [invoice.id])
                    wf_service.trg_validate(
                        uid, 'account.invoice', invoice.id, 'invoice_open',
                        cr)

        # Log a note in the contracts
        if contract_ids:
            self.pool.get('mail.thread').message_post(
                cr, uid, list(contract_ids),
                "The project was reactivated."
                "<br/>Invoices due in the suspension period "
                "are automatically reverted.",
                "Project Reactivated", 'comment',
                context={'thread_model': self._name})

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    def fields_view_get(self, cr, user, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        """ Display only contract type needed in view. """
        res = super(sponsorship_contract, self).fields_view_get(
            cr, user, view_id, view_type, context, toolbar, submenu)

        if view_type == 'form' and (isinstance(res['fields'], dict) and
                                    'type' in res['fields']):
            if 'S' in context.get('default_type', 'O'):
                # Remove non sponsorship types
                res['fields']['type']['selection'].pop(0)
                res['fields']['type']['selection'].pop(0)
            else:
                # Remove type Sponsorships so that we cannot change to it.
                res['fields']['type']['selection'].pop(2)
                res['fields']['type']['selection'].pop(2)
        return res

    def on_change_partner_id(self, cr, uid, ids, partner_id, type,
                             context=None):
        res = super(sponsorship_contract, self).on_change_partner_id(
            cr, uid, ids, partner_id, context)

        # Check if group_id is valid
        if 'group_id' in res['value']:
            if not self._is_a_valid_group(
                    cr, uid, res['value']['group_id'], context):
                del res['value']['group_id']

        if ids:
            contract = self.browse(cr, uid, ids[0], context)
            if 'S' in contract.type:
                # If state draft correspondant_id=partner_id
                if (contract.state == 'draft'):
                    res['value'].update({
                        'correspondant_id': partner_id,
                    })
        else:
            res['value'].update({
                'correspondant_id': partner_id,
            })

        return res

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    def contract_cancelled(self, cr, uid, ids, context=None):
        res = super(sponsorship_contract, self).contract_cancelled(
            cr, uid, ids, context)

        sponsorship_ids = self.search(cr, uid, [
            ('id', 'in', ids),
            ('type', 'like', 'S')], context=context)
        self._on_sponsorship_finished(cr, uid, sponsorship_ids, context)

        return res

    def contract_terminated(self, cr, uid, ids, context=None):
        res = super(sponsorship_contract, self).contract_terminated(
            cr, uid, ids, context)

        sponsorship_ids = self.search(cr, uid, [
            ('id', 'in', ids),
            ('type', 'like', 'S')], context=context)
        self._on_sponsorship_finished(cr, uid, sponsorship_ids, context)

        return res

    def contract_waiting_mandate(self, cr, uid, ids, context=None):
        for contract in self.browse(cr, uid, ids, context):
            # Check that a child is selected for Sponsorship product
            if 'S' in contract.type and not contract.child_id:
                raise orm.except_orm(
                    _("Please select a child"),
                    _("You should select a child if you "
                      "make a new sponsorship!"))
        return super(sponsorship_contract, self).contract_waiting_mandate(
            cr, uid, ids, context)

    def contract_waiting(self, cr, uid, ids, context=None):
        for contract in self.browse(cr, uid, ids, {'lang': 'en_US'}):
            if 'S' in contract.type and not contract.child_id:
                # Check that a child is selected for Sponsorship contract
                raise orm.except_orm(
                    _("Please select a child"),
                    _("You should select a child if you "
                      "make a new sponsorship!"))
            elif contract.type == 'G':
                # Activate directly if sponsorship is already active
                for line in contract.contract_line_ids:
                    sponsorship = line.sponsorship_id
                    if sponsorship.state == 'active':
                        cr.execute(
                            "update recurring_contract set "
                            "activation_date = current_date,is_active = True "
                            "where id = %s", [contract.id])
            elif contract.type == 'SC':
                # Activate directly correspondence sponsorships
                cr.execute(
                    "update recurring_contract set "
                    "activation_date = current_date,is_active = True "
                    "where id = %s", [contract.id])

        return super(sponsorship_contract, self).contract_waiting(
            cr, uid, ids, context)

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _on_sponsorship_finished(self, cr, uid, sponsorship_ids,
                                 context=None):
        """ Called when a sponsorship is terminated or cancelled:
        Remove sponsor from the child, terminate related gift
        contracts, and remove sponsor category if sponsor has no other
        active sponsorships.
        """
        ctx = {'lang': 'en_US'}
        category_obj = self.pool.get('res.partner.category')
        sponsor_cat_id = category_obj.search(
            cr, uid, [('name', '=', 'Sponsor')], context=ctx)[0]
        old_sponsor_cat_id = category_obj.search(
            cr, uid, [('name', '=', 'Old Sponsor')],
            context=ctx)[0]
        wf_service = netsvc.LocalService('workflow')
        con_line_obj = self.pool.get('recurring.contract.line')

        for sponsorship in self.browse(cr, uid, sponsorship_ids, context):
            sponsorship.child_id.write({'sponsor_id': False})

            con_ids = self.search(cr, uid, [
                ('partner_id', '=', sponsorship.partner_id.id),
                ('state', '=', 'active'),
                ('type', 'like', 'S')], context=context)
            if not con_ids:
                # Replace sponsor category by old sponsor category
                sponsorship.partner_id.write({
                    'category_id': [(3, sponsor_cat_id),
                                    (4, old_sponsor_cat_id)]})

            gift_con_ids = con_line_obj.search(cr, uid, [
                ('sponsorship_id', '=', sponsorship.id)], context=context)
            for line in con_line_obj.browse(cr, uid, gift_con_ids, context):
                contract = line.contract_id
                if len(contract.contract_line_ids) > 1:
                    line.unlink()
                else:
                    wf_service.trg_validate(
                        uid, self._name, contract.id,
                        'contract_terminated', cr)

    def _on_contract_active(self, cr, uid, ids, context=None):
        """ Hook for doing something when contract is activated.
        Update child to mark it has been sponsored, update partner
        to add the 'Sponsor' category, and activate gift contracts.
        """
        super(sponsorship_contract, self)._on_contract_active(cr, uid, ids,
                                                              context)
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
        con_line_obj = self.pool.get('recurring.contract.line')
        for contract in self.browse(cr, uid, ids, ctx):
            if 'S' in contract.type:
                contract.child_id.write({'has_been_sponsored': True})
                partner_categories = set(
                    [cat.id for cat in contract.partner_id.category_id
                     if cat.name != 'Old Sponsor'])
                partner_categories.add(sponsor_cat_id)
                # Standard way in Odoo to set one2many fields
                contract.partner_id.write({
                    'category_id': [(6, 0, list(partner_categories))]})
                gift_con_ids = con_line_obj.search(cr, uid, [
                    ('sponsorship_id', '=', contract.id)], context=context)
                for line in con_line_obj.browse(cr, uid, gift_con_ids, ctx):
                    wf_service.trg_validate(
                        uid, self._name, line.contract_id.id,
                        'contract_active', cr)

    def _on_change_child_id(self, cr, uid, ids, vals, context=None):
        """Link/unlink child to sponsor
        """
        child_id = vals.get('child_id')
        for contract in self.browse(cr, uid, ids, context):
            if 'S' in contract.type and contract.child_id and \
                    contract.child_id != child_id:
                # Free the previously selected child
                contract.child_id.write({'sponsor_id': False})
            if 'S' in contract.type:
                # Mark the selected child as sponsored
                self.pool.get('compassion.child').write(
                    cr, uid, child_id, {
                        'sponsor_id': vals.get('correspondant_id') or
                        contract.correspondant_id.id},
                    context)

    def _invoice_paid(self, cr, uid, invoice, context=None):
        """ Prevent to reconcile invoices for fund-suspended projects. """
        if invoice.payment_ids:
            for invl in invoice.invoice_line:
                if invl.contract_id and invl.contract_id.child_id:
                    payment_allowed = True
                    project = invl.contract_id.child_id.project_id

                    if invl.product_id.categ_name == GIFT_CATEGORY:
                        payment_allowed = project.disburse_gifts or \
                            invl.due_date < project.status_date
                    elif invl.product_id.categ_name == SPONSORSHIP_CATEGORY:
                        payment_allowed = project.disburse_funds or \
                            invl.due_date < project.status_date
                    if not payment_allowed:
                        raise orm.except_orm(
                            _("Reconcile error"),
                            _("The project %s is fund-suspended. You cannot "
                              "reconcile invoice (%s).") % (project.code,
                                                            invoice.id))

    def _is_a_valid_group(self, cr, uid, group_id, context=None):
        group_obj = self.pool.get('recurring.contract.group')
        group = group_obj.browse(cr, uid, group_id, context)

        if not group.contains_sponsorship or group.recurring_value != 1:
            return False
        return True

    def _has_valid_contract_lines(
            self, cr, uid, contract_lines, type, context=None):
        forbidden_product_types = {
            'O': [SPONSORSHIP_CATEGORY, GIFT_CATEGORY],
        }
        whitelist_product_types = {
            'G': [GIFT_CATEGORY],
            'S': [SPONSORSHIP_CATEGORY, FUND_CATEGORY],
            'SC': [SPONSORSHIP_CATEGORY, FUND_CATEGORY],
        }
        product_obj = self.pool.get('product.product')
        contract_lines = [cont_line[2] for cont_line in contract_lines
                          if cont_line[2]]

        for contract_line in contract_lines:
            product_id = contract_line.get('product_id')
            if product_id:
                product = product_obj.browse(
                    cr, uid, product_id, {'lang': 'en_US'})

                categ_name = product.categ_name
                allowed = whitelist_product_types.get(type)
                forbidden = forbidden_product_types.get(type)
                if (allowed and categ_name not in allowed) or \
                        (forbidden and categ_name in forbidden):
                    message = _('You can only select {0} products.').format(
                        str(allowed)) if allowed else _(
                        'You should not select product '
                        'from category "{0}"'.format(categ_name))
                    raise orm.except_orm(
                        _('Please select a valid product'), message)
        return True

    def update_next_invoice_date(self, cr, uid, ids, context=None):
        """ Override to force recurring_value to 1
            if contract is a sponsorship, and to bypass ORM for performance.
        """
        group_ids = list()
        for contract in self.browse(cr, uid, ids, context):
            group_ids.append(contract.group_id.id)
            if 'S' in contract.type:
                next_date = datetime.strptime(contract.next_invoice_date, DF)
                next_date += relativedelta(months=+1)
                next_date = next_date.strftime(DF)
            else:
                next_date = self._compute_next_invoice_date(contract)

            cr.execute(
                "UPDATE recurring_contract SET next_invoice_date = %s "
                "WHERE id = %s", (next_date, contract.id))
        self.pool.get('recurring.contract.group')._store_set_values(
            cr, uid, group_ids, ['next_invoice_date'], context)

        return True

    def _get_filtered_invoice_lines(
            self, cr, uid, invoice_lines, contract_id, context=None):
        res = list()
        for invl in invoice_lines:
            if (invl.contract_id == contract_id and
               invl.product_id.categ_name != GIFT_CATEGORY):
                res.append(invl.id)
        return res

    def _get_filtered_contract_ids(
            self, cr, uid, invoice_lines, context=None):
        res = list()
        for invl in invoice_lines:
            if (invl.contract_id and
               invl.product_id.categ_name != GIFT_CATEGORY):
                res.append(invl.contract_id.id)
        return res

    ##########################################################################
    #                      CLEAN PAID INVOICES METHODS                       #
    ##########################################################################
    def _filter_clean_invoices(self, cr, uid, ids, since_date=None,
                               to_date=None, gifts=False, context=None):
        """ Construct filter domain to be passed on method
        clean_invoices_paid, which will determine which invoice lines will
        be removed from invoices. """
        if not since_date:
            since_date = datetime.today().strftime(DF)
        invl_search = [('contract_id', 'in', ids), ('state', '=', 'paid'),
                       ('due_date', '>=', since_date),
                       ('product_id.categ_name', '!=', GIFT_CATEGORY)]
        if gifts:
            invl_search.pop()
        if to_date:
            invl_search.append(('due_date', '<=', to_date))

        return invl_search

    def _how_to_clean_invl(self, cr, uid, inv_line_ids, to_remove_inv,
                           to_update_inv, to_remove_mvl, to_remove_move,
                           to_update_mvl, split_payment_mvl, unrec_pml,
                           invl_rm_data, context=None):
        """ Determine which action has to be done for each invoice_line for
        method clean_invoices_paid. See that method for the parameters.
        """
        inv_line_obj = self.pool.get('account.invoice.line')
        for inv_line in inv_line_obj.browse(cr, uid, inv_line_ids, context):
            invoice = inv_line.invoice_id
            to_update_inv.add(invoice.id)
            if inv_line.contract_id.type == 'S':
                # Store data before removal
                invl_rm_data[inv_line.id] = [
                    invoice.id, inv_line.contract_id.child_code,
                    inv_line.product_id.name, inv_line.price_subtotal]

            mvl_found = False
            for mvl in inv_line.invoice_id.move_id.line_id:
                # 1. Update the move related with the invoice
                if not mvl_found and \
                        mvl.product_id.id == inv_line.product_id.id \
                        and mvl.credit == inv_line.price_subtotal \
                        and mvl.id not in to_remove_mvl:
                    # Mark mvl corresponding to invoice_line to be removed
                    to_remove_mvl.append(mvl.id)
                    mvl_found = True
                elif mvl.debit > 0 and mvl.account_id.code == '1050':
                    # Remove amount of invoice_line from debit line
                    # (the debit line corresponds to the total amount of
                    #  the invoice)
                    total_debit = to_update_mvl.get(mvl.id, mvl.debit)
                    to_update_mvl[mvl.id] = total_debit - \
                        inv_line.price_subtotal
                    if to_update_mvl[mvl.id] == 0:
                        # We deleted all invoice_lines and can delete the
                        # move associated with this invoice.
                        to_remove_mvl.append(mvl.id)
                        to_remove_move.append(mvl.move_id.id)

                    # 2. Update payment lines related with the invoice
                    for pml in mvl.reconcile_id.line_id:
                        if pml.credit > inv_line.price_subtotal:
                            amount_deleted = split_payment_mvl.get(pml.id,
                                                                   0.000)
                            split_payment_mvl[pml.id] = amount_deleted + \
                                inv_line.price_subtotal
                            if pml.credit == split_payment_mvl[pml.id]:
                                # The payment is fully unreconciled and thus
                                # don't need to be splitted
                                del split_payment_mvl[pml.id]
                                unrec_pml.append(pml.id)
                            elif pml.credit < split_payment_mvl[pml.id]:
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

        to_update_inv -= to_remove_inv

    def _clean_paid_invoice_lines(self, cr, uid, to_remove_inv, to_update_inv,
                                  inv_line_ids, keep_lines=None,
                                  context=None):
        """ Remove or cancel the invoice lines.
        - to_remove_inv : invoices which are totally cleaned
        - to_update_inv : invoices which still contains valid invoice_lines
        """
        invoice_obj = self.pool.get('account.invoice')
        inv_line_obj = self.pool.get('account.invoice.line')
        if keep_lines:
            # Cancel invoices instead of deleting them
            wf_service = netsvc.LocalService('workflow')
            invoice_obj.write(cr, uid, to_remove_inv, {
                'move_id': False}, context)
            for invoice_id in to_remove_inv:
                wf_service.trg_validate(uid, 'account.invoice',
                                        invoice_id, 'invoice_cancel', cr)
                self.pool.get('mail.thread').message_post(
                    cr, uid, invoice_id, keep_lines,
                    _("Invoice Cancelled"), 'comment',
                    context={'thread_model': 'account.invoice'})

            # Isolate invoice lines in cancelled invoices instead of
            # deleting them
            invl_to_cancel = [invl.id for invl in inv_line_obj.browse(
                cr, uid, inv_line_ids, context) if
                invl.invoice_id.id in to_update_inv]
            self._move_cancel_lines(cr, uid, invl_to_cancel, context,
                                    keep_lines)

        else:
            # Delete invoice lines and empty invoices
            cr.execute(
                "DELETE FROM account_invoice_line WHERE id in ({0})"
                .format(','.join(str(id) for id in inv_line_ids)))
            if to_remove_inv:
                cr.execute(
                    "DELETE FROM account_invoice WHERE id in ({0})"
                    .format(','.join(str(id) for id in to_remove_inv)))

    def _clean_move_lines(self, cr, to_remove_mvl, to_remove_move,
                          to_update_mvl):
        """ Remove move lines, invalid reconcile refs, empty moves and
        update total move lines of invoices after paid invoices were
        cleaned.
        """
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

    def _unrec_split_payment(self, cr, uid, payment_data, unrec_pml,
                             context=None):
        """ Method that splits a payment into two move_lines so that
        the amount which was cleaned from the paid invoice can be isolated
        and easily reconciled later.
        - payment_data (dict): {move_line_id: amount_cleaned}
        - unrec_pml (list): payment_lines which are totally unreconciled
        """
        mvl_obj = self.pool.get('account.move.line')
        for pml_id, amount_deleted in payment_data.iteritems():
            cr.execute(
                "UPDATE account_move_line SET credit=credit-{0:.3f} "
                "WHERE id = {1:d}".format(
                    amount_deleted,
                    pml_id))
            mvl_obj.copy(
                cr, uid, pml_id, default={
                    'reconcile_id': False,
                    'credit': amount_deleted}, context=context)

        if unrec_pml:
            mvl_obj._remove_move_reconcile(cr, uid, unrec_pml,
                                           context=context)
