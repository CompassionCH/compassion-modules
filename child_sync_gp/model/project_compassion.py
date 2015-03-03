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


class project_compassion(orm.Model):
    _inherit = 'compassion.project'

    def write(self, cr, uid, ids, vals, context=None):
        """Update Project in GP."""
        res = super(project_compassion, self).write(cr, uid, ids, vals,
                                                    context)
        gp_connect = gp_connector.GPConnect()
        for project in self.browse(cr, uid, ids, context):
            gp_connect.upsert_project(uid, project)
        return res
