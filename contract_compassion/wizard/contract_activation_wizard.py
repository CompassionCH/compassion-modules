# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

from datetime import datetime


class activate_contract_wizard(orm.TransientModel):
    """ This wizard force activation of a contract. """
    _name = 'recurring.contract.activate.wizard'

    def activate_contract(self, cr, uid, ids, context=None):
        contract_obj = self.pool.get('recurring.contract')
        # Ids of contracts are stored in context
        for contract in contract_obj.browse(
                cr, uid, context.get('active_ids', list()), context):
            if contract.state in ('draft', 'waiting'):
                contract.write({
                    'activation_date': datetime.today().strftime(DF)})
                contract_obj.force_activation(
                    cr, uid, contract.id, context)
        return True
