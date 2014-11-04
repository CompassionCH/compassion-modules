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

    """ Fizzbuzz performer.
        Args :
            - self : OpenObject reference (fizzbuzz).
            - cr : Database Cursor
            - uid : OpenERP User ID
            - ids : Ids of object for which to perform the fizzbuzz run
            - field_name : Name of the field that should be calculated
                           (will always be 'result' in our case)
            - arg : search criterias (not used in our case)
            - context : a dictionnary containing some context variables
                        (not used in our case)
        Returns :
            A dictionnary of the form :
                {id_1 : 'value_1', id_2 : 'value_2', ...}
    """
    def _perform_fizzbuzz(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for i in ids:
            # Retrieve OpenObject Fields
            fizz_params = self.browse(cr, uid, i)
            start = fizz_params.start   # nopep8
            end = fizz_params.end       # nopep8

            # Enter your code here
            res[i] = "Fizzbuzz !"
        return res

    _columns = {
        'name': fields.char("Name", size=128, required=True),
        'start': fields.integer("Start", size=128, required=True),
        'end': fields.integer("End", size=128),
        'result': fields.function(_perform_fizzbuzz, type="char", method=True,
                                  store=True, string="Result")
    }
