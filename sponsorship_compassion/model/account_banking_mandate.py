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

from openerp import api, models, netsvc


class account_mandate(models.Model):
    _inherit = 'account.banking.mandate'

    @api.multi
    def validate(self):
        """Validate LSV/DD Contracts when mandate is validated."""
        if super(account_mandate, self).validate():
            wf_service = netsvc.LocalService('workflow')
            for mandate in self:
                contract_ids = self.env['recurring.contract'].search(
                    [('partner_id', '=', mandate.partner_id.id),
                     ('state', '=', 'mandate')]).ids
                for con_id in contract_ids:
                    wf_service.trg_validate(
                        self.env.user.id, 'recurring.contract', con_id,
                        'mandate_validated', self.env.cr)
        return True
