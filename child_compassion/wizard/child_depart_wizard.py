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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _
from datetime import datetime

# Countries available for the child transfer
IP_COUNTRIES = ['AU', 'CA', 'DE', 'ES', 'FR', 'GB', 'IT', 'KR', 'NL',
                'NZ', 'US', 'NO']


class end_sponsorship_wizard(orm.TransientModel):
    _name = 'child.depart.wizard'

    def _get_child_id(self, cr, uid, context=None):
        # Retrieve the id of the child from context
        return context.get('active_id', False)

    def _get_exit_reason(self, cr, uid, context=None):
        res = self.pool.get('compassion.child').get_gp_exit_reasons(cr, uid)
        res.append(('transfer', _('Transfer')))
        return res

    _columns = {
        'end_date': fields.date(_('End date'), required=True),
        'child_id': fields.many2one('compassion.child', 'Child'),
        'transfer_country_id': fields.many2one(
            'res.country', _('Country'),
            domain=[('code', 'in', IP_COUNTRIES)]),
        'gp_exit_reason': fields.selection(
            _get_exit_reason, string=_('Exit reason'), required=True),
    }

    _defaults = {
        'child_id': _get_child_id,
        'end_date': datetime.today().strftime(DF),
    }

    def child_depart(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        vals = {'exit_date': wizard.end_date,
                'state': 'F'}

        # Child transfer
        if wizard.gp_exit_reason == 'transfer':
            vals['transfer_country_id'] = wizard.transfer_country_id.id
        # Other reasons
        else:
            vals['gp_exit_reason'] = wizard.gp_exit_reason

        return True
