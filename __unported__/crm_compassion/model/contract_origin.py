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


class contract_origin(orm.Model):
    """ Add event to origin of a contract """
    _inherit = 'recurring.contract.origin'

    _columns = {
        'event_id': fields.many2one('crm.event.compassion', _("Event")),
    }

    def _name_get(self, origin):
        if origin.type == 'event':
            name = origin.event_id.full_name
        else:
            name = super(contract_origin, self)._name_get(origin)
        return name


class contracts(orm.Model):
    """ Adds the Salesperson to the contract. """

    _inherit = 'recurring.contract'

    def _get_user_from_origin(self, origin):
        user_id = False
        if origin.partner_id:
            user_id = origin.partner_id.id
        elif origin.analytic_id and origin.analytic_id.manager_id:
            user_id = origin.analytic_id.manager_id.partner_id.id
        elif origin.event_id and origin.event_id.user_id:
            user_id = origin.event_id.user_id.partner_id.id
        return user_id

    _columns = {
        'user_id': fields.many2one('res.partner', _('Ambassador'))
    }

    def on_change_origin(self, cr, uid, ids, origin_id, context=None):
        origin = self.pool.get('recurring.contract.origin').browse(
            cr, uid, origin_id, context)
        return {
            'value': {'user_id': self._get_user_from_origin(origin)}
        }
