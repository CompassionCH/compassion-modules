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
            name = origin.event_id.name + " " + origin.event_id.start_date[:4]
        else:
            name = super(contract_origin, self)._name_get(origin)
        return name


class contracts(orm.Model):
    """ Adds the Salesperson to the contract. """

    _inherit = 'recurring.contract'

    def _get_user_id(self, cr, uid, ids, field_name, args, context=None):
        """ Finds the Salesperson of the contract. """
        res = dict()
        for contract in self.browse(cr, uid, ids, context):
            origin = contract.origin_id
            user_id = False
            if origin.partner_id:
                user_id = origin.partner_id.id
            elif origin.analytic_id and origin.analytic_id.manager_id:
                user_id = origin.analytic_id.manager_id.partner_id.id
            elif origin.event_id and origin.event_id.user_id:
                user_id = origin.event_id.user_id.partner_id.id
            res[contract.id] = user_id
        return res

    def _get_contracts_from_event(event_obj, cr, uid, ids, context=None):
        """Returns contracts originated by given events."""
        res = set()
        for event in event_obj.browse(cr, uid, ids, context):
            res.update([c.id for c in event.contract_ids])
        return list(res)

    _columns = {
        'user_id': fields.function(
            _get_user_id, type='many2one', obj='res.partner',
            string=_('Ambassador'), store={
                'recurring.contract': (
                    lambda self, cr, uid, ids, context=None: ids,
                    ['origin_id'],
                    10),
                'crm.event.compassion': (
                    _get_contracts_from_event,
                    ['user_id'],
                    10)})
    }
