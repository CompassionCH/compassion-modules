# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import models, fields, api


class EndContractWizard(models.TransientModel):
    _name = 'end.contract.wizard'

    contract_id = fields.Many2one(
        'recurring.contract', 'Contract',
        default=lambda self: self.env.context.get('active_id'))
    end_reason = fields.Selection(
        related='contract_id.end_reason', required=True)

    @api.multi
    def end_contract(self):
        # Terminate contract
        self.ensure_one()
        self.contract_id.signal_workflow('contract_terminated')
        return True
