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

from openerp.osv import orm, fields
from openerp.tools.translate import _
import pdb


class crm_lead(orm.Model):
    _inherit = "crm.lead"

    _columns = {
        'planned_sponsorships': fields.integer(
            _('Expected new sponsorships'), track_visibility='onchange'),
        'event_ids': fields.one2many(
            'crm.event.compassion', 'lead_id', _('Event'),
            readonly=True),
    }

    def create_event(self, cr, uid, ids, context=None):
        lead = self.browse(cr, uid, ids[0], context)
        context.update({
            'default_name': lead.name,
            'default_partner_id': lead.partner_id.id,
            'default_street': lead.street,
            'default_street2': lead.street2,
            'default_city': lead.city,
            'default_state_id': lead.state_id.id,
            'default_zip': lead.zip,
            'default_country_id': lead.country_id.id,
            'default_user_id': lead.user_id.id,
            'default_planned_sponsorships': lead.planned_sponsorships,
            'default_lead_id': lead.id
        })
        if lead.event_ids:
            model_event = lead.event_ids[-1]
            context['default_project_id'] = model_event.project_id.id
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
