# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import api, models, fields


class crm_lead(models.Model):
    _inherit = "crm.lead"

    planned_sponsorships = fields.Integer(
        'Expected new sponsorships', track_visibility='onchange')
    event_ids = fields.One2many(
        'crm.event.compassion', 'lead_id', 'Event',
        readonly=True)

    @api.multi
    def create_event(self):
        self.ensure_one()
        context = self.with_context({
            'default_name': self.name,
            'default_partner_id': self.partner_id.id,
            'default_street': self.street,
            'default_street2': self.street2,
            'default_city': self.city,
            'default_state_id': self.state_id.id,
            'default_zip': self.zip,
            'default_country_id': self.country_id.id,
            'default_user_id': self.user_id.id,
            'default_planned_sponsorships': self.planned_sponsorships,
            'default_lead_id': self.id,
            'default_project_id': self.event_ids and
            self.event_ids[-1].project_id.id or False}).env.context
        # Open the create form...
        return {
            'type': 'ir.actions.act_window',
            'name': 'New event',
            'view_type': 'form',
            'view_mode': 'form,calendar,tree',
            'res_model': 'crm.event.compassion',
            'target': 'current',
            'context': context,
        }
