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

from datetime import datetime, date
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
            if event.analytics_id:
                move_line_ids = mv_line_obj.search(cr, uid, [('analytics_id', '=', event.analytics_id.id)], context=context)
                res[event.id] = move_line_ids
            else:
                res[event.id] = False
                
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
        'move_line_ids': fields.function(_get_move_lines, type="one2many", relation="account.move.line", readonly=True),
        'planned_sponsorships': fields.integer(_("Expected sponsorships")),
        'lead_id': fields.many2one('crm.lead', _('Opportunity'), readonly=True),
    }
    
    def create(self, cr, uid, vals, context=None):
        """ When an event is created:
        - link it to the originating Opportunity,
        - create an analytic account,
        - create an origin for sponsorships.
        """
        new_id = super(event_compassion, self).create(cr, uid, vals, context)
        event = self.browse(cr, uid, new_id, context)
        if event.lead_id:
            event.lead_id.write({'event_id': new_id})

        origin_obj = self.pool.get('recurring.contract.origin')
        origin_id = origin_obj.create(cr, uid, {
            'name': event.name,
            'type': 'event',
            'partner_id': event.partner_id.id,
            'event_id': new_id,
        }, context)
        event.write({
            'origin_id': origin_id,
            'analytics_id': self._create_analytics(cr, uid, event.name, event.type, context)
        })
        return new_id

    def _create_analytics(self, cr, uid, event_name, event_type, context=None):
        """ Creates an analytic account together with an analytic distribution
        100% in the account, given the name and type of the event.
        """
        year = date.today().strftime('%y')
        acode = self.pool.get('ir.sequence').get(cr, uid, 'AASEQ')
        analytics_obj = self.pool.get('account.analytic.account')
        categ_id = analytics_obj.search(cr, uid, [('name', 'ilike', event_type)], context=context)[0]
        acc_ids = analytics_obj.search(cr, uid, [('name', '=', year), ('parent_id', '=', categ_id)], context=context)
        if not acc_ids:
            # The category for this year does not yet exist
            acc_ids = [analytics_obj.create(cr, uid, {
                'name': year,
                'type': 'view',
                'code': 'AA' + event_type[:2].upper() + year,
                'parent_id': categ_id
            }, context)]
        account_id = analytics_obj.create(cr, uid, {
            'name': event_name,
            'type': 'normal',
            'code': acode,
            'parent_id': acc_ids[0]
        }, context)
        plan_id = self.pool.get('account.analytic.plan.instance').create(cr, uid, {
            'name': year + '-' + event_name + ' Distribution',
            'code': acode,
            'journal_id': self.pool.get('ir.model.data').get_object(cr, uid, 'account', 'analytic_journal_sale', context).id
        }, context)
        self.pool.get('account.analytic.plan.instance.line').create(cr, uid, {
            'analytic_account_id': account_id,
            'rate': 100,
            'plan_id': plan_id
        }, context)

        return plan_id
        
