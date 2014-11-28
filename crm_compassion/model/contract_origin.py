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
