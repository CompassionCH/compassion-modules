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

from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp.osv import orm, fields
from openerp import netsvc
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import pdb


class crm_lead(orm.Model):
    _inherit = "crm.lead"
    
    def case_mark_won(self, cr, uid, ids, context=None):
        # Opportunity won, create an event based on its information
        pdb.set_trace()
        super(crm_lead, self).case_mark_won(cr, uid, ids, context)
        event_obj = self.pool.get('crm.event.compassion')
        if not isinstance(ids, list):
            ids = [ids]
        for lead in self.browse(cr, uid, ids, context):
            if lead.type == 'opportunity':
                event_id = event_obj.create(cr, uid, {
                    'name': lead.name,
                    'partner_id': lead.partner_id,
                    'street': lead.street,
                    'street2': lead.street2,
                    'city': lead.city,
                    'state_id': lead.state_id,
                    'zip': lead.zip,
                    'country_id': lead.country_id,
                    'user_id': lead.user_id,
                    'planned_sponsorships': lead.planned_sponsorship,
                }, context)
        # Open the last created Event for edit...
        res = {
            'type': 'ir.actions.act_window',
            'name': 'New event',
            'view_type': 'form',
            'view_mode': 'form,calendar,tree',
            'res_model': 'crm.event.compassion',
            'res_id': event_id,
            'target': 'current',
        } if event_id else True
        
        return res
