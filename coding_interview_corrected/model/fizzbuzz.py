# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp.osv import orm, fields


class fizzbuzz(orm.Model):
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

    def _perform_fizzbuzz_advanced(self, cr, uid, ids, fields_name, arg,
                                   context=None):
        res = {}
        for i in ids:
            fizz_params = self.browse(cr, uid, i)
            res[i] = ", ".join(
                [elem for elem in self._fizzbuzz_generator(fizz_params.start,
                                                           fizz_params.end)])
        return res

    def _fizzbuzz_generator(self, start, end):
        for i in range(start, end):
            if i % 3 == 0:
                yield "Fizzbuzz" if i % 5 == 0 else "Fizz"
            else:
                yield "Buzz" if i % 5 == 0 else str(i)

    _columns = {
        'result': fields.function(_perform_fizzbuzz, type="char", method=True,
                                  store=True, string="Result"),
        'result_advanced': fields.function(
            _perform_fizzbuzz_advanced, type="char", method=True, store=True,
            string="Advanced Result")
    }
