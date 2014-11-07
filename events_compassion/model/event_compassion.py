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


class event_compassion(orm.Model):
    """A Compassion event. """
    _name = "crm.event.compassion"
    _description = "Compassion event"
    
    _inherit = ['mail.thread']
    
    def _get_move_lines(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        mv_line_obj = self.pool.get('account.move.line')
        if not isinstance(ids, list):
            ids = [ids]
        for event in self.browse(cr, uid, ids, context):
            move_line_ids = mv_line_obj.search(cr, uid, [('analytics_id', '=', event.analytics_id.id)], context=context)
            res[event.id] = move_line_ids
        return res
    
    _columns = {
        'name': fields.char(_("Name"), size=128, required=True),
        'type': fields.selection([
            ('stand', _("Stand")),
            ('presentation', _("Presentation")),
            ('meeting', _("Meeting")),
            ('sport', _("Sport event"))], _("Type"), required=True),
        'start_date': fields.datetime(_("Start date"), required=True),
        'end_date': fields.datetime(_("End date")),
        'partner_id': fields.many2one('res.partner', _("Customer")),
        'zip_id': fields.many2one('res.better.zip', 'Address'),
        'street': fields.char('Street', size=128),
        'street2': fields.char('Street2', size=128),
        'city': fields.char('City', size=128),
        'state_id': fields.many2one('res.country.state', 'State'),
        'zip': fields.char('ZIP', size=24),
        'country_id': fields.many2one('res.country', 'Country'),
        'user_id': fields.many2one('res.users', _("Responsible")),
        'staff_ids': fields.many2many('res.partner', 'partners_to_staff_event', 'event_id', 'partner_id', _("Staff")),
        'description': fields.text('Description'),
        'analytics_id': fields.many2one('account.analytic.plan.instance', 'Analytic Distribution'),
        'origin_id': fields.many2one('recurring.contract.origin', 'Origin'),
        'contract_ids': fields.related('origin_id', 'contract_ids', type="one2many", relation="recurring.contract", readonly=True),
        'move_line_ids': fields.function(_get_move_lines, type="one2many"),
        'planned_sponsorships': fields.integer(_("Expected sponsorships")),
        'lead_id': fields.many2one('crm.lead', _('Opportunity'), readonly=True),
    }
    
    _defaults = {
        'name': '/',
        'type': 'presentation',
        'start_date': datetime.today().strftime(DF),
    }
