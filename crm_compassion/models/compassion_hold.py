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
from openerp import api, models, fields

from openerp.addons.child_compassion.models.compassion_hold import HoldType


class CompassionHold(models.Model):
    _inherit = 'compassion.hold'

    origin_id = fields.Many2one('recurring.contract.origin',
                                compute='_compute_origin', store=True)
    event_id = fields.Many2one('crm.event.compassion', 'Event',
                               track_visibility='onchange')

    @api.multi
    @api.depends('channel', 'type', 'event_id', 'ambassador')
    def _compute_origin(self):
        origin_obj = self.env['recurring.contract.origin']
        for hold in self:
            origin_search = list()
            if hold.type == HoldType.REINSTATEMENT_HOLD.value:
                origin_search.append(('name', '=', 'Reinstatement'))
            elif hold.channel == 'event' and hold.event_id:
                origin_search.append(('event_id', '=', hold.event_id.id))
            elif hold.channel == 'ambassador' and hold.ambassador:
                origin_search.append(('name', '=', hold.ambassador.name))
            elif hold.channel == 'web':
                origin_search.append(('name', '=', 'Internet'))
            if origin_search:
                hold.origin_id = origin_obj.search(origin_search, limit=1)


class ChildCompassion(models.Model):
    _inherit = 'compassion.child'

    hold_event = fields.Many2one(related='hold_id.event_id', store=True)


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
