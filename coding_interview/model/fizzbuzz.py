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

class fizzbuzz(osv.osv):
    """ A fizzbuzz model """
    _name = 'interview.fizzbuzz'
    
    """ Fizzbuzz performer.
        Args :
            - self : OpenObject reference (fizzbuzz).
            - cr : Database Cursor
            - uid : OpenERP User ID
            - ids : Ids of object for which to perform the fizzbuzz run
            - field_name : Name of the field that should be calculated (will always be 'result' in our case)
            - arg : search criterias (not used in our case)
            - context : a dictionnary containing some context variables (not used in our case)
        Returns :
            A dictionnary of the form :
                {id_1 : 'value_1', id_2 : 'value_2', ...} 
    """
    def _perform_fizzbuzz(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for i in ids:
            # Retrieve OpenObject Fields
            fizz_params = self.browse(cr, uid, i)
            start = fizz_params.start
            end = fizz_params.end
            
            # Enter your code here
            res[i] = "Fizzbuzz !"
        return res
    
    
    _columns = {
        'name': fields.char("Name",size=128,required=True),
        'start': fields.integer("Start",size=128,required=True),
        'end': fields.integer("End",size=128),
        'result': fields.function(_perform_fizzbuzz, type="char", method=True, store=True, string="Result")
    }
    
fizzbuzz()