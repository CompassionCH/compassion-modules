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

from openerp import models, api


class activate_contract_wizard(models.TransientModel):
    """ This wizard force activation of a contract. """
    _name = 'recurring.contract.activate.wizard'

    @api.multi
    def activate_contract(self):
        contract_obj = self.env['recurring.contract']
        # Ids of contracts are stored in context
        for contract in contract_obj.browse(
                self.env.context.get('active_ids', list())):
            if contract.state in ('draft', 'waiting'):
                contract.force_activation()
        return True
