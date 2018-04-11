# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016-2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api, fields, _


class ChildHoldWizard(models.TransientModel):
    _inherit = 'child.hold.wizard'

    campaign_id = fields.Many2one('utm.campaign', 'Campaign')

    @api.model
    def get_action_selection(self):
        selection = super(ChildHoldWizard, self).get_action_selection()
        selection.append(('event', _('Go back to event')))
        return selection

    @api.multi
    def get_hold_values(self):
        hold_vals = super(ChildHoldWizard, self).get_hold_values()

        event_id = self.env.context.get('event_id')
        if event_id:
            hold_vals['event_id'] = event_id
        return hold_vals

    def _get_action(self, holds):
        action = super(ChildHoldWizard, self)._get_action(holds)
        if self.return_action == 'event':
            action.update({
                'res_model': 'crm.event.compassion',
                'res_id': self.env.context.get('event_id'),
                'view_mode': 'form,tree',
            })
        return action
