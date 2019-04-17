# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api
from ..mappings.compassion_project_mapping import MobileProjectMapping


class CompassionProject(models.Model):
    ''' A Compassion project '''
    _inherit = 'compassion.project'

    @api.multi
    def get_app_json(self, multi=False):
        """
        Called by HUB when data is needed for a tile
        :param multi: used to change the wrapper if needed
        :return: dictionary with JSON data of the children
        """
        if not self:
            return {}
        mapping = MobileProjectMapping(self.env)
        if len(self) == 1:
            data = mapping.get_connect_data(self)
        else:
            data = []
            for child in self:
                data.append(mapping.get_connect_data(child))
        return data

    @api.model
    def mobile_get_project(self, **other_params):
        """
        Mobile app method:
        Returns the project for a given fcp ID.
        :param fcpid: the id of the church associated with the project
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

        project = self.search([
            ('fcp_id', '=', icpid)
        ], limit=1)

        mapping = MobileProjectMapping(self.env)
        if project:
            result['ProjectServiceResult']['ICPResponseList'] = (
                mapping.get_connect_data(project))
        return result

    def _get_required_param(self, key, params):
        if key not in params:
            raise ValueError('Required parameter {}'.format(key))
        return params[key]
