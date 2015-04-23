# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm, fields
from openerp.tools.translate import _


class contract_group(orm.Model):
    _inherit = 'recurring.contract.group'

    def _contains_sponsorship(
            self, cr, uid, ids, field_name, args, context=None):
        res = dict()
        for group in self.browse(cr, uid, ids, context):
            for contract in group.contract_ids:
                if contract.type == 'S':
                    res[group.id] = True
                    break
            else:
                res[group.id] = False

        return res

    _columns = {
        'contains_sponsorship': fields.function(
            _contains_sponsorship, string=_('Contains sponsorship'),
            type='boolean', readonly=True)
    }
