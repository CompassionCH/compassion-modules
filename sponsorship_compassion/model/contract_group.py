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
            if group.contract_ids:
                for contract in group.contract_ids:
                    if contract.type == 'S':
                        res[group.id] = True
                        break
                else:
                    res[group.id] = False
            else:
                res[group.id] = True
        return res

    _columns = {
        'contains_sponsorship': fields.function(
            _contains_sponsorship, string=_('Contains sponsorship'),
            type='boolean', readonly=True)
    }

    def _setup_inv_line_data(self, cr, uid, contract_line, invoice_id,
                             context=None):
        """ Contract gifts relate their invoice lines to sponsorship. """
        invl_data = super(contract_group, self)._setup_inv_line_data(
            cr, uid, contract_line, invoice_id, context)

        contract = contract_line.contract_id
        if contract.type == 'G':
            sponsorship = contract_line.sponsorship_id
            if sponsorship.state in self._get_gen_states():
                invl_data['contract_id'] = sponsorship.id
            else:
                raise orm.except_orm(
                    _('Invoice generation error'),
                    _('No active sponsorship found for child {0}. '
                      'The gift contract with id {1} is not valid.').format(
                        sponsorship.child_code, str(contract.id))
                )

        return invl_data
