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

from openerp import models, api


class account_mandate(models.Model):
    _inherit = 'account.banking.mandate'

    @api.multi
    def validate(self):
        """Validate LSV/DD Contracts when mandate is validated."""
        super(account_mandate, self).validate()
        self._trigger_contracts('mandate', 'mandate_validated')
        return True

    @api.multi
    def cancel(self):
        """Set back contracts in waiting mandate state."""
        super(account_mandate, self).cancel()
        self._trigger_contracts('active', 'will_pay_by_lsv_dd')
        return True

    @api.multi
    def _trigger_contracts(self, state, transition):
        """ Fires a given transition on contracts in selected state. """
        contracts = self.env['recurring.contract']
        for mandate in self:
            contracts |= contracts.search(
                [('partner_id', 'child_of', mandate.partner_id.id),
                 ('state', '=', state)])
        contracts.signal_workflow(transition)
