# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester <csester@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
from openerp.osv import orm, fields
from openerp import netsvc
import openerp.exceptions
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

logger = logging.getLogger(__name__)


class res_partner(orm.Model):
    ''' Override partners to add contract m2o relation. Raise an error if
    we try to delete a partner with active contracts.
    '''
    _inherit = 'res.partner'

    _columns = {
        'contract_group_ids': fields.one2many(
            'simple.recurring.contract.group', 'partner_id',
            _('Contract groups')),
    }

    def unlink(self, cr, uid, ids, context=None):
        ''' Raise an error if there is active contracts for partner '''
        if context is None:
            context = {}
        partners = self.browse(cr, uid, ids, context=context)
        unlink_ids = []

        contract_obj = self.pool.get('simple.recurring.contract')

        for partner in partners:
            for contract_group in partner.contract_group_ids:
                for contract in contract_group.contract_ids:
                    if contract.state not in ('draft', 'terminated'):
                        raise orm.except_orm(
                            'UserError',
                            _('You cannot delete a partner having an active '
                              'contract.'))
            unlink_ids.append(partner.id)

        super(res_partner, self).unlink(cr, uid, unlink_ids, context=context)
        return True


class simple_recurring_contract_line(orm.Model):
    ''' Each product sold through a contract '''
    _name = "simple.recurring.contract.line"
    _description = "A contract line"
    _rec_name = 'product_id'

    def _compute_subtotal(self, cr, uid, ids, field_name, arg, context):
        res = {}
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids, context=context):
            price = line.amount * line.quantity
            res[line.id] = price
        return res

    _columns = {
        'contract_id': fields.many2one(
            'simple.recurring.contract', _('Contract'), required=True,
            ondelete='cascade', readonly=True),
        'product_id': fields.many2one(
            'product.product', _('Product'), required=True),
        'amount': fields.float(_('Price'), required=True),
        'quantity': fields.integer(_('Quantity'), required=True),
        'subtotal': fields.function(
            _compute_subtotal, string='Subtotal', type="float",
            digits_compute=dp.get_precision('Account'), store=True),
    }

    _defaults = {
        'quantity': 1,
    }

    def on_change_product_id(self, cr, uid, ids, product_id, context=None):
        context = context or {}

        if not product_id:
            return {'value': {'amount': 0.0}}

        prod = self.pool.get('product.product').browse(cr, uid, product_id,
                                                      context=context)
        value = {'amount': prod.list_price or 0.0}

        return {'value': value}


class simple_recurring_contract(orm.Model):
    ''' A contract to perform recurring invoicing to a partner '''
    _name = "simple.recurring.contract"
    _description = "Contract for recurring invoicing"
    _inherit = ['mail.thread']
    _rec_name = 'reference'

    def _get_total_amount(self, cr, uid, ids, name, args, context=None):
        con_line_obj = self.pool.get('simple.recurring.contract.line')
        total = {}
        for contract in self.browse(cr, uid, ids, context):
            total[contract.id] = sum([line.subtotal
                                      for line in contract.contract_line_ids])

        return total

    _columns = {
        'reference': fields.char(
            _('Reference'), required=True, readonly=True,
            states={'draft':[('readonly',False)]}),
        'start_date': fields.date(
            _('Start date'), required=True, readonly=True,
            states={'draft':[('readonly',False)]}),
        'end_date': fields.date(
            _('End date'), readonly=False,
            states={'terminated':[('readonly',True)]}),
        'next_invoice_date': fields.date(
            _('Next invoice date'), readonly=False,
            states={'draft':[('readonly',False)]}),
        'partner_id': fields.many2one(
            'res.partner', _('Partner'), required=True, readonly=True,
            states={'draft':[('readonly',False)]}, ondelete='cascade'),
        'group_id': fields.many2one(
            'simple.recurring.contract.group', _('Group'),
            required=True, ondelete='cascade'),
        'invoice_line_ids': fields.one2many(
            'account.invoice.line', 'contract_id',
            _('Related invoice lines'), readonly=True),
        'contract_line_ids': fields.one2many(
            'simple.recurring.contract.line', 'contract_id',
            _('Contract lines')),
        'state': fields.selection([
            ('draft', _('Draft')),
            ('active', _('Active')),
            ('terminated', _('Terminated')),
            ], _('Status'), select=True,
            readonly=True, track_visibility='onchange',
            help=_(" * The 'Draft' status is used when a user is encoding a "
                   "new and unconfirmed Contract.\n"
                   "* The 'Active' status is used when the contract is "
                   "confirmed and until it's terminated.\n"
                   "* The 'Terminated' status is used when a contract is no "
                   "longer active.")),
        'payment_term_id': fields.many2one('account.payment.term',
                                           _('Payment Term')),
        'advance_billing': fields.selection([
            ('bimonthly', _('Bimonthly')),
            ('quarterly', _('Quarterly')),
            ('fourmonthly', _('Four-monthly')),
            ('biannual', _('Bi-annual')),
            ('annual', _('Annual'))], _('Advance billing'), readonly=True,
            states={'draft':[('readonly',False)]},
            help = _('Advance billing allows you to generate invoices in '
                     'advance. For example, you can generate the invoices '
                     'for each month of the year and send them to the '
                     'customer in january.')),
        # Tools for advance billing
        'next_advance_date': fields.date('Next advance date', readonly=True),
        'is_advance': fields.boolean('is advance'),
        'total_amount': fields.function(
            _get_total_amount, string='Total',
            digits_compute = dp.get_precision('Account'),
            store = {
                'simple.recurring.contract': (lambda self, cr, uid, ids, c={}: 
                                              ids, ['contract_line_ids'], 20),
                }),
    }

    _defaults = {
        'reference': '/',
        'state': 'draft',
        'recurring_unit': 'month',
        'recurring_value': 1,
        'is_advance': False,
    }

    def _check_unique_reference(self, cr, uid, ids, context=None):
        sr_ids = self.search(cr, 1 ,[], context=context)
        lst = [contract.reference
               for contract in self.browse(cr, uid, sr_ids, context=context)
               if contract.reference and contract.id not in ids
              ]
        for self_contract in self.browse(cr, uid, ids, context=context):
            if self_contract.reference and self_contract.reference in lst:
                return False
        return True

    _constraints = [(_check_unique_reference,
                     _('Error: Reference should be unique'), ['reference'])]

    #################################
    #        PUBLIC METHODS         #
    #################################
    def create(self, cr, uid, vals, context=None):
        if vals.get('reference', '/') == '/':
            vals['reference'] = self.pool.get('ir.sequence').next_by_code(
                    cr, uid, 'simple.rec.contract.ref', context=context)
        if not vals['next_advance_date']:
            vals['next_advance_date'] = vals['next_invoice_date']
        return super(simple_recurring_contract, self).create(cr, uid, vals,
                                                             context=context)

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        contracts = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []

        for contract in contracts:
            if contract['state'] not in ('draft', 'terminated'):
                raise orm.except_orm(
                    'UserError',
                    _('You cannot delete a contract that is still active. '
                      'Terminate it first.'))
            else:
                unlink_ids.append(contract['id'])

        super(simple_recurring_contract, self).unlink(cr, uid, unlink_ids,
                                                      context=context)
        return

    def clean_invoices(self, cr, uid, ids, context=None, since_date=None):
        ''' This method deletes invoices lines generated for a given contract 
            having a due date > since_date. If the invoice_line was the only 
            line in the invoice, we cancel the invoice. In the other case, we 
            have to revalidate the invoice to update the invoice lines.
        '''
        logger.info("%s" % ids)
        logger.info("Start clean")
        if not since_date:
            since_date = datetime.today().strftime(DEFAULT_SERVER_DATE_FORMAT)
            
        inv_line_obj = self.pool.get('account.invoice.line')
        inv_obj = self.pool.get('account.invoice')
        wf_service = netsvc.LocalService('workflow')
        
        # Find all unpaid invoice lines after the given date
        inv_line_ids = inv_line_obj.search(cr, uid, [('contract_id', 'in', ids), ('due_date', '>', since_date), ('state', '!=', 'paid')], context=context)
        inv_ids = set()
        for inv_line in inv_line_obj.browse(cr, uid, inv_line_ids, context):
            inv_ids.add(inv_line.invoice_id.id)
        
        if inv_line_ids: #To prevent remove all inv_lines...
            inv_line_obj.unlink(cr, uid, inv_line_ids, context)
        
        inv_ids = list(inv_ids)
        inv_obj.action_cancel(cr, uid, inv_ids, context=context)

        empty_inv_ids = []
        for inv in inv_obj.browse(cr, uid, inv_ids, context):
            if not inv.invoice_line:
                empty_inv_ids.append(inv.id)
        renew_inv_ids = list(set(inv_ids)-set(empty_inv_ids))
                
        inv_obj.action_cancel_draft(cr, uid, renew_inv_ids)
        for inv in inv_obj.browse(cr, uid, renew_inv_ids, context):
            wf_service.trg_validate(uid, 'account.invoice', inv.id, 'invoice_open', cr)

        logger.info("End clean")
        
    #################################
    #        PRIVATE METHODS        #
    #################################
    def _compute_next_invoice_date(self, contract):
        next_date = datetime.strptime(contract.next_invoice_date, DEFAULT_SERVER_DATE_FORMAT)
        if contract.recurring_unit == 'day':
            next_date = next_date + relativedelta(days=+contract.recurring_value)
        elif contract.recurring_unit == 'week':
            next_date = next_date + relativedelta(weeks=+contract.recurring_value)
        elif contract.recurring_unit == 'month':
            next_date = next_date + relativedelta(months=+contract.recurring_value)
        else:
            next_date = next_date + relativedelta(years=+contract.recurring_value)
            
        return next_date
        
    def _get_group_fields(self):
        ''' Return a string formatted list of fields that are passed to the orm
            search method. In order to group invoice line, they have to be sorted 
            by ``common´´ fields. If you want to add new grouping conditions, you 
            should inherit this method and append the concerned fields to the 
            string
        '''
        group_fields = 'partner_id, payment_term_id, next_invoice_date'
        return group_fields
        
    def _get_search_args(self):
        ref_date = (datetime.today()+relativedelta(months=1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
        args = ['&', ('state', '=', 'active'), '|', ('next_invoice_date', '<=', ref_date), 
               ('is_advance', '=', True)]
        return args
    
    def _match_conditions(self, conditions, contract):
        match = contract.next_invoice_date == conditions['invoice_date']
        match &= contract.partner_id.id == conditions['partner_id']
        match &= contract.payment_term_id.id == conditions['payment_term_id']

        return match   
        
    def _setup_conditions(self):
        ''' Setup grouping conditions. The dict is then used in _match_conditions
            to determine if 2 contract can be grouped. Inherit to add/remove 
            conditions.
        '''
        conditions = {
            'partner_id': None,
            'payment_term_id': None,
            'invoice_date': None,
            }
            
        return conditions

    def _update_conditions(self, conditions, contract):
        ''' When a new group of invoice lines is created, update conditions
            values to fit new group values. Inherit to handle your own conditions.
        '''
        conditions.update({
            'partner_id': contract.partner_id.id,
            'payment_term_id': contract.payment_term_id and contract.payment_term_id.id or '',
            'invoice_date': contract.next_invoice_date,
            })
        
        return conditions
    
    ##########################
    #        CALLBACKS       #
    ##########################        
    def on_change_start_date(self, cr, uid, ids, start_date, context=None):
        result = {}
        if start_date:
            result.update({'next_invoice_date': start_date})
            result.update({'next_advance_date': start_date})
        
        return {'value': result}
        
    def on_change_next_invoice_date(self, cr, uid, ids, next_invoice_date, advance_billing, context=None):
        result = {}
        if advance_billing and next_invoice_date:
            result.update({'next_advance_date': next_invoice_date})
            
        return {'value': result}

    def contract_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'}, context=context)
        return True

    def contract_active(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'active'}, context=context)
        return True

    def contract_terminated(self, cr, uid, ids, context=None):
        today = datetime.today().strftime(DEFAULT_SERVER_DATE_FORMAT)
        self.write(cr, uid, ids, {'state': 'terminated', 'end_date': today})
        return True
        
    def end_date_reached(self, cr, uid, context=None):
        today = datetime.today().strftime(DEFAULT_SERVER_DATE_FORMAT)
        contract_ids = self.search(cr, uid, [('state', '=', 'active'), ('end_date', '<=', today)], context=context)
        
        if contract_ids:
            self.contract_terminated(cr, uid, contract_ids, context=context)
        
        return True
        