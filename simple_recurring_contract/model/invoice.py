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
from openerp.osv import orm, fields
from openerp.tools.translate import _

class account_invoice(orm.Model):
    _name = 'account.invoice'
    _inherit = 'account.invoice'
    
    _columns = {
        'recurring_invoicer_id': fields.many2one('recurring.invoicer', _('Invoicer')),
    }    
    
class account_invoice_line(orm.Model):
    _name = 'account.invoice.line'
    _inherit = 'account.invoice.line'
    
    def _get_dates(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context):
            res[line.id] = line.invoice_id.date_due
            
        return res
        
    def _get_states(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context):
            res[line.id] = line.invoice_id.state
            
        return res
    
    def _get_invoice_lines(self, cr, uid, ids, context=None):
        inv_line_obj = self.pool.get('account.invoice.line')
        inv_line_ids = inv_line_obj.search(cr, uid, [('invoice_id', 'in', ids)], context=context)
        return inv_line_ids
    
    _columns = {
        'contract_id': fields.many2one('simple.recurring.contract', _('Source contract')),
        'due_date': fields.function(_get_dates, string=_('Due date'), readonly=True, type='date',
                                    store={'account.invoice': (_get_invoice_lines, ['date_due'], 20)}),
        'state': fields.function(_get_states, string=_('State'), readonly=True, type='selection', \
                                selection=[('draft','Draft'), ('proforma','Pro-forma'), ('proforma2','Pro-forma'), \
                                            ('open','Open'), ('paid','Paid'), ('cancel','Cancelled'),], 
                                            store={'account.invoice': (_get_invoice_lines, ['state'], 20)}),
    }