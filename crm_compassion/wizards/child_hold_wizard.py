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
from odoo import models, api, _


class ChildHoldWizard(models.TransientModel):
    _inherit = 'child.hold.wizard'

    @api.model
    def get_action_selection(self):
        selection = super(ChildHoldWizard, self).get_action_selection()
        selection.append(('event', _('Go back to event')))
        return selection

    def _get_action(self, holds):
        action = super(ChildHoldWizard, self)._get_action(holds)
        if self.return_action == 'event':
            action.update({
                'res_model': 'crm.event.compassion',
                'res_id': self.env.context.get('event_id'),
                'view_mode': 'form,tree',
            })
        return action
