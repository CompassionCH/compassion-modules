# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Emanuel Cino. Copyright Compassion Suisse
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
from openerp.osv import osv, fields
import sys
import pdb

class equilibrium(osv.osv):
    """ A equilibrium model """
    _name = 'interview.equilibrium'
    
    def _perform_equilibrium(self, cr, uid, ids, fields_name, arg, context=None):
        res = {}
        result = ""
        for i in ids:
            A = [int(x) for x in self.browse(cr, uid, ids)[0].list.split(',')]
            minDiff = sys.maxint
            diff = minDiff
            for j in range(1, len(A)):
                first = A[:j]
                second = A[j:]
                diff = abs(sum(first) - sum(second))
                if diff < minDiff:
                    minDiff = diff
            res[i] = minDiff
                            
        return res
        
    _columns = {
        'name': fields.char("Name",size=128,required=True),
        'list': fields.char("List",size=128,required=True),
        'result': fields.function(_perform_equilibrium, type="integer", method=True, store=True, string="Result")
    }
    
equilibrium()