# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi. Copyright Camptocamp SA
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
import re
import logging

from openerp.osv.orm import Model, fields
from openerp.tools import mod10r

logger = logging.getLogger(__name__)

class account_invoice(Model):
    ''' Inherit account.invoice in order to change BVR ref field type '''
    _inherit = "account.invoice"

    _columns = {
        'bvr_reference': fields.char("BVR REF.", size=32,)
    }
    
    def _check_bvr_ref(self, cr, uid, ids, context=None):
        record = self.browse(cr, uid, ids, context=context)
        for data in record:
            if not data.bvr_reference:
                return True #No check if no reference
            clean_ref = data.bvr_reference.replace(' ', '')
            if not clean_ref.isdigit() or len(clean_ref) > 27:
                return False
            clean_ref = clean_ref.rjust(27, '0') #Add zeros to the left
            if not clean_ref == mod10r(clean_ref[0:26]):
                return False
                
        return True
    
    _constraints = [
        (_check_bvr_ref, 'Error: BVR ref should only contain number (max. 27) and spaces.', ['bvr_reference'])]
        
    def _get_bvr_ref(self, cr, uid, invoice, context=None):
        ''' Overload to take manual bvr ref if exists '''
        if invoice.bvr_reference:
            return invoice.bvr_reference
        else:
            return super(account_invoice, self)._get_bvr_ref(cr, uid, invoice, context)
        
class account_move_line(Model):
    _inherit = 'account.move.line'
    def get_bvr_ref(self, cursor, uid, move_line_id, context=None):
        ''' Overload to take manual bvr ref if exists '''
        if isinstance(move_line_id, (tuple, list)):
            assert len(move_line_id) == 1, "Only 1 ID expected"
            move_line_id = move_line_id[0]

        move_line = self.browse(cursor, uid, move_line_id, context=context)
        ## We check if the type is bvr, if not we return false
        if move_line.invoice.bvr_reference:
            return move_line.invoice.bvr_reference
        else:
            return super(account_move_line, self).get_bvr_ref(cursor, uid, move_line_id, context)
            