##############################################################################
#
#    Copyright (C) 2016-2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api, fields


class ChildHoldWizard(models.TransientModel):
    _inherit = 'child.hold.wizard'

    return_action = fields.Selection(
        selection_add=[('event', 'Go back to event')])

    def _get_action(self, holds):
        action = super()._get_action(holds)
        if self.return_action == 'event':
            action.update({
                'res_model': 'crm.event.compassion',
                'res_id': self.env.context.get('event_id'),
                'view_mode': 'form,tree',
            })
        return action
