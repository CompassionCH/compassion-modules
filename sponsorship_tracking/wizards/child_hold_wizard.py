# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import api, models, _


class ChildHoldWizard(models.TransientModel):
    """ Add return action for sub_sponsorship. """
    _inherit = 'child.hold.wizard'

    @api.model
    def get_action_selection(self):
        selection = super(ChildHoldWizard, self).get_action_selection()
        selection.append(('sub', _('Make SUB Sponsorship')))
        return selection

    @api.multi
    def send(self):
        """ Remove default_type from context to avoid putting type in child.
        """
        return super(ChildHoldWizard, self.with_context(
            default_type='CDSP')).send()

    def _get_action(self, holds):
        action = super(ChildHoldWizard, self)._get_action(holds)
        if self.return_action == 'sub':
            sub_contract = self.env['recurring.contract'].browse(
                self.env.context.get('contract_id'))
            sub_contract.write({'child_id': holds[0].child_id.id})
            sub_contract.signal_workflow('contract_validated')
            sub_contract.next_invoice_date = self.env.context.get(
                'next_invoice_date')
            action.update({
                'res_model': 'recurring.contract',
                'res_id': sub_contract.id,
                'view_mode': 'form',
            })
            action['context'] = self.with_context({
                'default_type': 'S',
            }).env.context
        return action
