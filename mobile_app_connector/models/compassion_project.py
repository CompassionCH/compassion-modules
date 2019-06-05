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
from ..mappings.compassion_project_mapping import MobileProjectMapping, \
    MobileLocationMapping


class CompassionProject(models.Model):
    ''' A Compassion project '''
    _inherit = 'compassion.project'

    @api.multi
    def get_location_json(self, multi=False):
        """
        Called by HUB when data is needed for a tile
        :param multi: used to change the wrapper if needed
        :return: dictionary with JSON data of the children
        """
        if not self:
            return {}
        mapping = MobileLocationMapping(self.env)
        # Location is only supported for one child (we take the first if
        # we have many children)
        data = mapping.get_connect_data(self[:1])
        return data

    @api.multi
    def get_weather_json(self, multi=False):
        if not self:
            return {}
        self.update_weather()
        return {
            'ChildWeather': self.current_weather,
            'ChildTemperature': self.current_temperature,
            # the following fields are not used but prevent app crashes
            'UserWeather': self.current_weather,
            'UserTemperature': self.current_temperature,
        }

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
    def mobile_get_project(self, **params):
        """
        Mobile app method:
        Returns the project for a given fcp ID.
        :param params: all GET parameters
        :return: JSON containing the project
        """
        result = {
            'ProjectServiceResult': {
                'Error': None,
                'ICPResponseList': []
            }
        }

        project = self.search([
            ('fcp_id', '=', self._get_required_param('IcpId', params))
        ], limit=1)

        mapping = MobileProjectMapping(self.env)
        if project:
            result['ProjectServiceResult']['ICPResponseList'] = [(
                mapping.get_connect_data(project))]
        return result

    def _get_required_param(self, key, params):
        if key not in params:
            raise ValueError('Required parameter {}'.format(key))
        return params[key]
