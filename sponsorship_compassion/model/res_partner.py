# -*- coding: utf-8 -*-
##############################################################################
#
#    Authors: Cyril Sester, Emanuel Cino
#    Copyright Compassion Suisse
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
import logging

logger = logging.getLogger(__name__)

class res_partner(orm.Model):
    _inherit = 'res.partner'
    
    def _get_related_contracts(self, cr, uid, ids, field_name, arg, context):
        """
        Returns the contracts of the sponsor of given type ('fully_managed', 'correspondant' or 'payer')
        """
        res = {}
        contract_obj = self.pool.get('simple.recurring.contract')
        for id in ids:
            correspondant_ids = contract_obj.search(cr, uid, [('correspondant_id', '=', id),('fully_managed', '=', False)], context={})
            paid_ids = contract_obj.search(cr, uid, [('partner_id', '=', id),('fully_managed', '=', False)], context={})
            fully_managed_ids = contract_obj.search(cr, uid, [('partner_id', '=', id),('fully_managed', '=', True)], context={})
            
            if field_name == 'contracts_fully_managed':
                res[id] = fully_managed_ids
            elif field_name == 'contracts_paid':
                res[id] = paid_ids
            elif field_name == 'contracts_correspondant':
                res[id] = correspondant_ids
        
        return res

    def _write_related_contracts(self, cr, uid, id, name, value, inv_arg, context=None):
        value_obj = self.pool.get('simple.recurring.contract')
        for line in value:
            if line[0] == 1: # on2many update
                value_id = line[1]
                value_obj.write(cr, uid, [value_id], line[2])
        return True
    
    _columns = {
        'contracts_fully_managed' : fields.function(
            _get_related_contracts, type="one2many",
            obj="simple.recurring.contract",
            fnct_inv=_write_related_contracts,
            string='Contracts'),
        'contracts_paid' : fields.function(
            _get_related_contracts, type="one2many",
            obj="simple.recurring.contract",
            fnct_inv=_write_related_contracts,
            string='Contracts'),
        'contracts_correspondant' : fields.function(
            _get_related_contracts, type="one2many",
            obj="simple.recurring.contract",
            fnct_inv=_write_related_contracts),
    }
    
    def show_lines(self, cr, uid, ids, context=None):
        inv_obj = self.pool.get('account.invoice')
        inv_line_obj = self.pool.get('account.invoice.line')
        inv_ids = inv_obj.search(cr, uid, [('partner_id', '=', ids[0])], context=context)
        inv_line_ids = inv_line_obj.search(cr, uid, [('invoice_id', 'in', inv_ids)], context=context)
        try:
            ir_model_data = self.pool.get('ir.model.data')
            invoice_line_id = ir_model_data.get_object_reference(
                cr, uid, 'sponsorship_compassion', 'view_invoice_line_partner_tree'
            )[1]
        except ValueError:
            invoice_line_id = False
        
        action = {
            'name': 'Related invoice lines',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree, form',
            'domain': [('id', 'in', inv_line_ids)],
            'res_model': 'account.invoice.line',
            'view_id': invoice_line_id,
            'views': [(invoice_line_id, 'tree'), (False, 'form')],
            'target': 'current',
            }
            
        return action
