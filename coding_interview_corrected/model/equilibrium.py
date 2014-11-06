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
import sys


class equilibrium(orm.Model):
    """ A equilibrium model """
    _name = 'interview.equilibrium'

    def _perform_equilibrium(self, cr, uid, ids, fields_name, arg,
                             context=None):
        res = {}
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
        'name': fields.char("Name", size=128, required=True),
        'list': fields.char("List", size=128, required=True),
        'result': fields.function(
            _perform_equilibrium, type="integer", method=True, store=True,
            string="Result")
    }
