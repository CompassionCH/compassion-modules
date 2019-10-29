# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields
from odoo.addons.crm.models.crm_lead import CRM_LEAD_FIELDS_TO_MERGE


class CrmLead(models.Model):
    _inherit = "crm.lead"

    planned_sponsorships = fields.Integer(
        'Expected new sponsorships', track_visibility='onchange')
    event_ids = fields.One2many(
        'crm.event.compassion', 'lead_id', 'Events')
    phonecall_ids = fields.One2many('crm.phonecall', 'opportunity_id')
    meeting_ids = fields.One2many('calendar.event', 'opportunity_id')

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

    @api.multi
    def _merge_data(self, fields):
        """ Update the _merge_data function to be able to merge
        many2many and one2may

            :param fields: list of fields to process
            :return dict data: contains the merged values of
            the new opportunity
        """
        data = super(CrmLead, self)._merge_data(fields)

        for field_name in fields:
            field = self._fields.get(field_name)
            if field.type in ('many2many', 'one2many'):
                data[field_name] = [(6, 0, self.mapped(field_name).ids)]

        return data

    @api.multi
    def merge_opportunity(self, user_id=False, team_id=False):
        CRM_LEAD_FIELDS_TO_MERGE.extend(['phonecall_ids', 'meeting_ids'])
        return super(CrmLead, self).merge_opportunity(
            user_id, team_id)
