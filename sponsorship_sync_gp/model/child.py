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

from openerp.osv import orm

from . import gp_connector


class child_compassion(orm.Model):
    _inherit = 'compassion.child'

    def write(self, cr, uid, ids, vals, context=None):
        """ When child state is changed because of
        a sponsorship, update GP. """
        res = super(child_compassion, self).write(cr, uid, ids, vals, context)
        if 'state' in vals.keys():
            gp_connect = gp_connector.GPConnect(cr, uid)
            for child in self.browse(cr, uid, ids, context):
                gp_connect.set_child_sponsor_state(child)

        return res
