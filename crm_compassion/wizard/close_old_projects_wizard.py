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

from datetime import date


class close_projects_wizard(orm.TransientModel):
    _name = 'project.close.wizard'

    def close_projects(self, cr, uid, ids, context=None):
        """ Find projects with no tasks which end_date is past
        and close them. """
        project_obj = self.pool.get('project.project')
        project_ids = project_obj.search(cr, uid, [
            ('state', '=', 'open'),
            '|', ('date', '<', date.today()),
            '&', ('date', '=', False),
            ('date_start', '<', date.today()),
            ('tasks', '=', False),
            ], context=context)
        if project_ids:
            project_obj.set_done(cr, uid, project_ids, context)

        return True
