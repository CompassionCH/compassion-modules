# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm
from openerp.tools.translate import _


class res_partner(orm.Model):
    _inherit = 'res.partner'

    def open_events(self, cr, uid, ids, context=None):
        event_ids = self.pool.get('crm.event.compassion').search(
            cr, uid, [('partner_id', 'child_of', ids)], context=context)

        return {
            'name': _('Events'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'crm.event.compassion',
            'target': 'current',
            'domain': [('id', 'in', event_ids)],
            'context': context,
        }
