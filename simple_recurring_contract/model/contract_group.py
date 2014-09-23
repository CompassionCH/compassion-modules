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

from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _


class contract_group(orm.Model):
    _name = 'simple.recurring.contract.group'
    _desc = 'A group of contracts'

    _columns = {
        # TODO sequence for name/ref ?
        'recurring_unit': fields.selection([
            ('day', _('Day(s)')),
            ('week', _('Week(s)')),
            ('month', _('Month(s)')),
            ('year', _('Year(s)'))], _('Reccurency'), required=True,
            readonly=True, states={'draft':[('readonly', False)]}),
        'recurring_value': fields.integer(
            _('Generate every'), required=True, readonly=True,
            states={'draft':[('readonly', False)]}),
        'partner_id': fields.many2one(
            'res.partner', _('Partner'), required=True, readonly=True,
            states={'draft':[('readonly', False)]}, ondelete='cascade'),
        'contract_ids': fields.one2many(
            'simple.recurring.contract', 'group_id', _('Contracts'),
            readonly=True),
    }

    def generate_invoices(self, cr, uid, ids, invoicer_id=None,
                          is_group=False, context=None):
        ''' Checks all contracts and generate invoices if next_invoice_date
        is reached.
        Create an invoice per contract group.
        '''
        inv_obj = self.pool.get('account.invoice')
        journal_obj = self.pool.get('account.journal')
        contract_obj = self.pool.get('simple.recurring.contract')
        
        journal_ids = journal_obj.search(
            cr, uid, [('type', '=','sale'),('company_id', '=', 1 or False)],
            limit=1)
        for contract_group in self.browse(cr, uid, ids, context):
            group_inv_date = contract_group.next_invoice_date
            logger.info("%s, %s" % (group_inv_date, type(group_inv_date)))
            contr_ids = [contract.id
                            if contract.next_invoice_date < group_inv_date
                            for contract in contract_group.contract_ids]
            if not contr_ids:
                continue

            inv_data = self._setup_inv_data(cr, uid, contract_group,
                                            journal_ids, invoicer_id,
                                            context=context)
            invoice_id = inv_obj.create(cr, uid, inv_data, context=context)

            for contract in contract_obj.browse(cr, uid, contr_ids, context):
                self._generate_invoice_lines(cr, uid, contract, invoice_id,
                                             context)

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

    def _setup_inv_data(self, cr, uid, con_gr, journal_ids,
                        invoicer_id, context=None):
        ''' Setup a dict with data passed to invoice.create.
            If any custom data is wanted in invoice from contract group, just
            inherit this method.
        '''
        today = datetime.today().strftime(DF)
        partner = con_gr.partner_id

        inv_data = {
            'account_id': partner.property_account_receivable.id,
            'type': 'out_invoice',
            'partner_id': partner.id,
            'journal_id': len(journal_ids) and journal_ids[0] or False,
            'currency_id': partner.property_product_pricelist.currency_id.id \
                            or False,
            'date_invoice': con_gr.next_invoice_date,
            'recurring_invoicer_id': invoicer_id,
            'payment_term': con_gr.payment_term_id \
                                and con_gr.payment_term_id.id or False,
            }

        return inv_data

    def _setup_inv_line_data(self, cr, uid, contract_line, invoice_id,
                             context=None):
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

    def _generate_invoice_lines(self, cr, uid, contract, invoice_id,
                               context=None):
        inv_line_obj = self.pool.get('account.invoice.line')
        for contract_line in contract.contract_line_ids:
            inv_line_data = self._setup_inv_line_data(cr, uid, contract_line,
                                                      invoice_id, context)
            inv_line_obj.create(cr, uid, inv_line_data, context=context)

        vals = {}

        next_date = self._compute_next_invoice_date(contract)
        vals['next_invoice_date'] = next_date.strftime(DF)
        
        #If contract has advance billing, update it to next delay
        if contract.advance_billing and \
                next_date > datetime.strptime(contract.next_advance_date, DF):
            delay_dict = {'annual': 12, 'biannual': 6, 'fourmonthly': 4,
                          'quarterly': 3, 'bimonthly' : 2}
            next_advance_date = datetime.strptime(contract.next_advance_date,
                                                  DF)
            next_advance_date = next_advance_date + relativedelta(months=+delay_dict[contract.advance_billing])
            vals['next_advance_date'] = next_advance_date.strftime(DF)
            contract.next_advance_date = next_advance_date.strftime(DF)
           
        #If contract has advance billing, put the flag to indicate that next invoices have to be generate
        if contract.advance_billing \
            and next_date < datetime.strptime(contract.next_advance_date, DEFAULT_SERVER_DATE_FORMAT) \
            and (not contract.end_date or next_date < datetime.strptime(contract.end_date, DEFAULT_SERVER_DATE_FORMAT)):
            vals['is_advance'] = True
        else:
            vals['is_advance'] = False
            
        self.write(cr, uid, [contract.id], vals)
