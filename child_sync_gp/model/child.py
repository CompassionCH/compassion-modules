# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
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
        if 'state' in vals:
            gp_connect = gp_connector.GPConnect()
            for child in self.browse(cr, uid, ids, context):
                gp_connect.set_child_sponsor_state(child)

        return res

    def create(self, cr, uid, vals, context=None):
        """Push new child into GP."""
        new_id = super(child_compassion, self).create(cr, uid, vals, context)
        child = self.browse(cr, uid, new_id, context)
        gp_connect = gp_connector.GPConnect()
        gp_connect.upsert_child(uid, child)
        return new_id


class child_properties(orm.Model):
    _inherit = 'compassion.child.properties'

    def create(self, cr, uid, vals, context=None):
        """Push new case study into GP."""
        new_id = super(child_properties, self).create(cr, uid, vals, context)
        case_study = self.browse(cr, uid, new_id, context)
        gp_connect = gp_connector.GPConnect()
        gp_connect.upsert_case_study(uid, case_study)
        return new_id

    def write(self, cr, uid, ids, vals, context=None):
        """ Update GP with new values of Case Study. """
        res = super(child_properties, self).write(cr, uid, ids, vals, context)
        gp_connect = gp_connector.GPConnect()
        for case_study in self.browse(cr, uid, ids, context):
            gp_connect.upsert_case_study(uid, case_study)
        return res
