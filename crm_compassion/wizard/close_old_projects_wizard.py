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

from openerp import api, models

from datetime import date


class close_projects_wizard(models.TransientModel):
    _name = 'project.close.wizard'

    @api.multi
    def close_projects(self):
        """ Find projects with no tasks which end_date is past
        and close them. """
        projects = self.env['project.project'].search([
            ('state', '=', 'open'),
            '|', ('date', '<', date.today()),
            '&', ('date', '=', False),
            ('date_start', '<', date.today()),
            ('tasks', '=', False)])
        if projects:
            projects.set_done()

        return True
