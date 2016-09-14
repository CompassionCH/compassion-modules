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
from openerp import api, models, fields, exceptions, _
from datetime import datetime, timedelta
from openerp.exceptions import Warning


class CompassionHold(models.Model):
    _inherit = 'compassion.hold'

    event_id = fields.Many2one('crm.event.compassion', 'Event', readonly=True)


class ChildHoldWizard(models.TransientModel):
    _inherit = 'child.hold.wizard'

    @api.multi
    def get_hold_values(self):
        hold_vals = super(ChildHoldWizard, self).get_hold_values()

        event_id = self.env.context.get('event_id')
        if event_id:
            hold_vals['event_id'] = event_id
        return hold_vals

    @api.multi
    def send(self):
        action = super(ChildHoldWizard, self).send()

        if self.env.context.get('event_id') is None:
            return action
        else:
            del action['domain']
            action.update({
                'view_mode': 'form,tree',
                'res_model': 'crm.event.compassion',
                'res_id': self.env.context.get('event_id')
            })
            return action
