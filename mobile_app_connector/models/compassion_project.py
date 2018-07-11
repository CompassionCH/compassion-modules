# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging


from odoo import models, api
from ..mappings.compassion_project_mapping import MobileProjectMapping


class CompassionProject(models.Model):
    ''' A Compassion project '''
    _inherit = 'compassion.project'

    @api.model
    def mobile_get_project(self, icpid=None, **other_params):
        """
        Mobile app method:
        Returns the project for a given ICP ID.
        :param icpid: the id of the church associated with the project
        :param other_params: all request parameters
        :return: JSON containing the project
        """
        result = {
            'ProjectServiceResult': {
                'Error': None,
                'ICPResponseList': None
            }
        }
        if icpid is None:
            return result

        projects = self.env['compassion.project'].search([
            ('icp_id', '=', icpid)
        ], limit=1)

        mapping = MobileProjectMapping(self.env)
        if projects:
            result['ProjectServiceResult']['ICPResponseList'] = (
                mapping.get_connect_data(projects[0]))

        result = result
        return result
