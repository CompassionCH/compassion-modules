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
    def mobile_get_project(self, **other_params):
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
        icpid = self._get_required_param('icpid', other_params)
        if icpid is None:
            return result

        projects = self.search([
            ('icp_id', '=', icpid)
        ], limit=1)

        mapping = MobileProjectMapping(self.env)
        if projects:
            result['ProjectServiceResult']['ICPResponseList'] = (
                mapping.get_connect_data(projects[0]))
        return result

    def _get_required_param(self, key, params):
        if key not in params:
            raise ValueError('Required parameter {}'.format(key))
        return params[key]
