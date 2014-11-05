# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Wulliamoz <dwulliamoz@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import fields, orm


class crm_lead(orm.Model):
    """ CRM Lead Case """
    _inherit = "crm.lead"
    _name = "crm.lead"

    _columns = {
        'planned_sponsorship': fields.integer(
            'Expected new sponsorship', track_visibility='always'),
    }
