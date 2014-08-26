# -*- encoding: utf-8 -*-
##############################################################################
#
#    Recurring contract module for openERP
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    @author: Cyril Sester <csester@compassion.ch>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
    _name = 'res.partner'
    _inherit = 'res.partner'
    
    _columns = {
        'contract_ids': fields.one2many('simple.recurring.contract', 'partner_id', _('Contracts')),
    }
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        partners = self.read(cr, uid, ids, ['contract_ids'], context=context)
        unlink_ids = []
        
        contract_obj = self.pool.get('simple.recurring.contract')

        for t in partners:
            for contract in contract_obj.read(cr, uid, t['contract_ids'], ['state'], context=context):
                if contract['state'] not in ('draft', 'terminated'):
                    raise openerp.exceptions.Warning(_('You cannot delete a partner having an active contract.'))
            unlink_ids.append(t['id'])

        super(res_partner, self).unlink(cr, uid, unlink_ids, context=context)
        return True
    
class simple_recurring_contract_line(orm.Model):
    _name = "simple.recurring.contract.line"
    _description = "A contract line"
    _rec_name = 'product_id'
    
    def _compute_subtotal(self, cr, uid, ids, field_name, arg, context):
        res = {}
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids):
            price = line.amount * line.quantity
            res[line.id] = price
        return res
    
    _columns = {
        'contract_id': fields.many2one('simple.recurring.contract', _('Contract'), required=True, ondelete='cascade', readonly=True),
        'product_id': fields.many2one('product.product', _('Product'), required=True),
        'amount': fields.float(_('Price'), required=True),
        'quantity': fields.integer(_('Quantity'), required=True),
        'subtotal': fields.function(_compute_subtotal, string='Subtotal', type="float",
            digits_compute=dp.get_precision('Account'), store=True),
        }
    
    _defaults = {
        'quantity': 1,
    }
        
    def on_change_product_id(self, cr, uid, ids, product, context=None):
        context = context or {}

        if not product:
            return {'value': {'amount': 0.0}}

        result = {}
        res = self.pool.get('product.product').browse(cr, uid, product, context=context)
        result.update({'amount': res.list_price or 0.0})

        res_final = {'value':result}
        return res_final
        
simple_recurring_contract_line()    
    
class simple_recurring_contract(orm.Model):
    _name = "simple.recurring.contract"
    _description = "Recurrent invoicing with contracts"
    _inherit = ['mail.thread']
    _rec_name = 'reference'
    
    def _get_total_amount(self, cr, uid, ids, name, args, context=None):
        con_line_obj = self.pool.get('simple.recurring.contract.line')
        total = {}
        for id in ids:
            contract = self.browse(cr, uid, id, context)
            total[id] = sum([line.subtotal for line in contract.contract_line_ids])
            
        return total
    
    _columns = {
        'reference': fields.char(_('Reference'), required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'start_date': fields.date(_('Start date'), required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'end_date': fields.date(_('End date'), readonly=False, states={'terminated':[('readonly',True)]}),
        'recurring_unit': fields.selection([
            ('day', _('Day(s)')),
            ('week', _('Week(s)')),
            ('month', _('Month(s)')),
            ('year', _('Year(s)'))], _('Reccurency'), required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'recurring_value': fields.integer(_('Generate every'), required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'next_invoice_date': fields.date(_('Next invoice date'), readonly=False, states={'draft':[('readonly',False)]}),
        'partner_id': fields.many2one('res.partner', _('Partner'), required=True, readonly=True, states={'draft':[('readonly',False)]}, ondelete='cascade'),
        'invoice_line_ids': fields.one2many('account.invoice.line', 'contract_id', _('Related invoice lines'), readonly=True),
        'contract_line_ids': fields.one2many('simple.recurring.contract.line', 'contract_id', _('Contract lines')),
        'state': fields.selection([
            ('draft', _('Draft')),
            ('active', _('Active')),
            ('terminated', _('Terminated')),
            ], _('Status'), select=True, readonly=True, track_visibility='onchange',
            help=_(' * The \'Draft\' status is used when a user is encoding a new and unconfirmed Contract.\n' \
                    '* The \'Active\' status is used when the contract is confirmed and until it\'s terminated.\n' \
                    '* The \'Terminated\' status is used when a contract is no longer active.')),
        'payment_term_id': fields.many2one('account.payment.term', _('Payment Term')),
        'advance_billing': fields.selection([
            ('bimonthly', _('Bimonthly')),
            ('quarterly', _('Quarterly')),
            ('fourmonthly', _('Four-monthly')),
            ('biannual', _('Bi-annual')),
            ('annual', _('Annual'))], _('Advance billing'), readonly=True, states={'draft':[('readonly',False)]},
            help = _('Advance billing allows you to generate invoices in advance. For example, you can generate ' \
                    'the invoices for each month of the year and send them to the customer in january.')),
        'next_advance_date': fields.date('Next advance date', readyonly=True), #Tool for advance billing
        'is_advance': fields.boolean('is advance'), #Tool for advance billing
        'total_amount': fields.function(_get_total_amount, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'simple.recurring.contract': (lambda self, cr, uid, ids, c={}: ids, ['contract_line_ids'], 20),
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
        lst = [
                contract.reference for contract in self.browse(cr, uid, sr_ids, context=context)
                if contract.reference and contract.id not in ids
              ]
        for self_contract in self.browse(cr, uid, ids, context=context):
            if self_contract.reference and self_contract.reference in lst:
                return False
        return True
    
    _constraints = [(_check_unique_reference, _('Error: Reference should be unique'), ['reference'])]
    
    #################################
    #        PUBLIC METHODS         #
    #################################
    def create(self, cr, uid, vals, context=None):
        if vals.get('reference', '/') == '/':
            vals['reference'] = self.pool.get('ir.sequence').next_by_code(
                    cr, uid, 'simple.rec.contract.ref', context=context)
        if not vals['next_advance_date']:
            vals['next_advance_date'] = vals['next_invoice_date']
        return super(simple_recurring_contract, self).create(cr, uid, vals, context=context)
        
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        contracts = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []

        for t in contracts:
            if t['state'] not in ('draft', 'terminated'):
                raise openerp.exceptions.Warning(_('You cannot delete a contract that is still active. Terminate it first.'))
            else:
                unlink_ids.append(t['id'])

        super(simple_recurring_contract, self).unlink(cr, uid, unlink_ids, context=context)
        return 
    
    def generate_invoices(self, cr, uid, ids, invoicer_id=None, is_group=False, context=None):
        '''Checks all contracts and generate invoices if next_invoice_date in reached.
            Each contract returns an invoice line. This way, if some grouping is needed, it can be done here.
        '''
        
        logger.info("start generate")
        
        inv_obj = self.pool.get('account.invoice')
        journal_obj = self.pool.get('account.journal')
        
        journal_ids = journal_obj.search(cr, uid, [('type', '=','sale'),('company_id', '=', 1 or False)], limit=1)
        group_fields = self._get_group_fields()
        contract_ids = self.search(cr, uid, args = self._get_search_args(),
                                   order=group_fields, context=context)      
        
        #We loop in case of multiple invoices should be generated for same contract
        while contract_ids:
            if isinstance(contract_ids, (int, long)):
                contract_ids = [contract_ids]
                        
            conditions = self._setup_conditions()
            current_invoice_id = None
            for contract in self.browse(cr, uid, contract_ids, context):
                if not is_group or not self._match_conditions(conditions, contract): 
                    #Compute total for previous and create new invoice
                    if current_invoice_id:
                        inv_obj.button_compute(cr, uid, [current_invoice_id], context=context)
                        
                    inv_data = self._setup_inv_data(cr, uid, contract, journal_ids, invoicer_id, context=context)
                    current_invoice_id = inv_obj.create(cr, uid, inv_data, context=context)
                    conditions = self._update_conditions(conditions, contract)
                    
                #And invoice line within the contract
                self._generate_invoice_line(cr, uid, contract, current_invoice_id, context)
            
            if current_invoice_id:
                inv_obj.button_compute(cr, uid, [current_invoice_id], context=context)
                
            #We look again for contracts to handle and loop again over them if necessary
            contract_ids = self.search(cr, uid, 
                args = self._get_search_args(), 
                order=group_fields, context=context) 
                
        logger.info("End generate")
        
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
    def _generate_invoice_line(self, cr, uid, contract, invoice_id, context=None):
        for contract_line in contract.contract_line_ids:
            inv_line_data = self._setup_inv_line_data(cr, uid, contract_line, invoice_id, context=context)
            self.pool.get('account.invoice.line').create(cr, uid, inv_line_data, context=context)
        
        vals = {}
        
        next_date = self._compute_next_invoice_date(contract)
        vals['next_invoice_date'] = next_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
        
        #If contract has advance billing, update it to next delay
        if contract.advance_billing \
            and next_date > datetime.strptime(contract.next_advance_date, DEFAULT_SERVER_DATE_FORMAT):
            delay_dict = {'annual': 12, 'biannual': 6, 'fourmonthly': 4, 'quarterly': 3, 'bimonthly' : 2}
            next_advance_date = datetime.strptime(contract.next_advance_date, DEFAULT_SERVER_DATE_FORMAT)
            next_advance_date = next_advance_date + relativedelta(months=+delay_dict[contract.advance_billing])
            vals['next_advance_date'] = next_advance_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
            contract.next_advance_date = next_advance_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
           
        #If contract has advance billing, put the flag to indicate that next invoices have to be generate
        if contract.advance_billing \
            and next_date < datetime.strptime(contract.next_advance_date, DEFAULT_SERVER_DATE_FORMAT) \
            and (not contract.end_date or next_date < datetime.strptime(contract.end_date, DEFAULT_SERVER_DATE_FORMAT)):
            vals['is_advance'] = True
        else:
            vals['is_advance'] = False
            
        self.write(cr, uid, [contract.id], vals)
        
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
        
    def _setup_inv_data(self, cr, uid, contract, journal_ids, invoicer_id, context=None):
        ''' Setup a dict with data passed to invoice.create.
            If any custom data is wanted in invoice from contract, just
            inherit this method.
        '''
        today = datetime.today().strftime(DEFAULT_SERVER_DATE_FORMAT)
        pay_term_obj = self.pool.get('account.payment.term')

        inv_data = {
            'account_id': contract.partner_id.property_account_receivable.id,
            'type': 'out_invoice',
            'partner_id': contract.partner_id.id,
            'journal_id': len(journal_ids) and journal_ids[0] or False,
            'currency_id': contract.partner_id.property_product_pricelist.currency_id.id or False,
            'date_invoice': contract.next_invoice_date,
            'recurring_invoicer_id': invoicer_id,
            'payment_term': contract.payment_term_id and contract.payment_term_id.id or False,
            }

        return inv_data
        
    def _setup_inv_line_data(self, cr, uid, contract_line, invoice_id, context=None):
        ''' Setup a dict with data passed to invoice_line.create.
            If any custom data is wanted in invoice line from contract,
            just inherit this method.
        '''
        product = contract_line.product_id

        inv_line_data = {
            'name': product.name,
            'account_id': product.property_account_income.id,
            'price_unit': contract_line.amount or 0.0,
            'quantity': contract_line.quantity,
            'uos_id': False,
            'product_id': product.id or False,
            'invoice_id' : invoice_id,
            'contract_id': contract_line.contract_id.id,
        }
        
        return inv_line_data
        
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
        