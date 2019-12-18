##############################################################################
#
#    Copyright (C) 2016-2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields

from odoo.addons.child_compassion.models.compassion_hold import HoldType


class AbstractHold(models.AbstractModel):
    _inherit = 'compassion.abstract.hold'

    campaign_id = fields.Many2one('utm.campaign', 'Campaign')
    event_id = fields.Many2one('crm.event.compassion', 'Event')

    def get_fields(self):
        _fields = super().get_fields()
        return _fields + ['campaign_id', 'event_id']

    def get_hold_values(self):
        """ Get the field values of one record.
            :return: Dictionary of values for the fields
        """
        vals = super().get_hold_values()
        event = vals.get('event_id')
        if event:
            vals['event_id'] = event[0]
        campaign = vals.get('campaign_id')
        if campaign:
            vals['campaign_id'] = campaign[0]
        return vals


class CompassionHold(models.Model):
    _inherit = 'compassion.hold'

    origin_id = fields.Many2one('recurring.contract.origin',
                                compute='_compute_origin', store=True)
    event_id = fields.Many2one(track_visibility='onchange')

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
        res_ids = super().reservation_to_hold(commkit_data)
        for hold in self.browse(res_ids):
            hold.event_id = hold.reservation_id.event_id
            hold.campaign_id = hold.reservation_id.campaign_id
        return res_ids


class ChildCompassion(models.Model):
    _inherit = 'compassion.child'

    hold_event = fields.Many2one(related='hold_id.event_id', store=True)
    campaign_id = fields.Many2one(related='hold_id.campaign_id')


class Reservation(models.Model):
    _inherit = 'compassion.reservation'

    event_id = fields.Many2one('crm.event.compassion', 'Event')
    campaign_id = fields.Many2one('utm.campaign', 'Campaign')
