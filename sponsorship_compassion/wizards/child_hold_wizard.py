# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, _


class ChildHoldWizard(models.TransientModel):
    """ Add return action for sponsoring selected child. """
    _inherit = 'child.hold.wizard'

    @api.model
    def get_action_selection(self):
        selection = super(ChildHoldWizard, self).get_action_selection()
        selection.append(('sponsor', _('Sponsor the child')))
        return selection

    def _get_action(self, holds):
        action = super(ChildHoldWizard, self)._get_action(holds)
        if self.return_action == 'sponsor':
            child = holds[0].child_id
            action.update({
                'name': _('Sponsor the child on hold'),
                'res_model': 'recurring.contract',
                'res_id': self.env.context.get('contract_id'),
                'view_mode': 'form',
            })
            action['context'] = self.with_context({
                'default_child_id': child.id,
                'child_id': child.id,
                'default_type': 'S',
            }).env.context
        return action

    @api.multi
    def send(self):
        if self.return_action == 'sponsor':
            return super(ChildHoldWizard,
                         self.with_context(async_mode=False)).send()
        else:
            return super(ChildHoldWizard, self).send()
