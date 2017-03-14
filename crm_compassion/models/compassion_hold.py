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
from openerp import api, models, fields, _

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

    def reservation_to_hold(self, commkit_data):
        res_ids = super(CompassionHold, self).reservation_to_hold(commkit_data)
        for hold in self.browse(res_ids):
            hold.event_id = hold.reservation_id.event_id
        return res_ids


class ChildCompassion(models.Model):
    _inherit = 'compassion.child'

    hold_event = fields.Many2one(related='hold_id.event_id', store=True)


class ChildHoldWizard(models.TransientModel):
    _inherit = 'child.hold.wizard'

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


class Reservation(models.Model):
    _inherit = 'compassion.reservation'

    event_id = fields.Many2one('crm.event.compassion', 'Event')
