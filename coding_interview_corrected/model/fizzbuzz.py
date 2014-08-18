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
    _inherit = 'interview.fizzbuzz'
    
    def _perform_fizzbuzz(self, cr, uid, ids, fields_name, arg, context=None):
        res = {}
        result = ""
        for i in ids:
            fizz_params = self.browse(cr, uid, i)
            for j in range(fizz_params.start, fizz_params.end):
                if j % 3 == 0:
                    result += "Fizzbuzz, " if j % 5 == 0 else "Fizz, "
                    continue
                if j % 5 == 0:
                    result += "Buzz, "
                    continue
                result += "%i, " % j
                    
            res[i] = result
        return res
    
    def _perform_fizzbuzz_advanced(self, cr, uid, ids, fields_name, arg, context=None):
        res = {}
        for i in ids:
            fizz_params = self.browse(cr, uid, i)
            res[i] = ", ".join([elem for elem in self._fizzbuzz_generator(fizz_params.start, fizz_params.end)])
        return res
        
    def _fizzbuzz_generator(self, start, end):
        for i in range(start, end):
            if i % 3 == 0:
                yield "Fizzbuzz" if i % 5 == 0 else "Fizz"
            else: yield "Buzz" if i % 5 == 0 else str(i)
        
    _columns = {
        'result': fields.function(_perform_fizzbuzz, type="char", method=True, store=True, string="Result"),
        'result_advanced': fields.function(_perform_fizzbuzz_advanced, type="char", method=True, store=True, string="Advanced Result")
    }
    
fizzbuzz()