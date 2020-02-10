##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api


class CompassionProject(models.Model):
    """A Compassion project """
    _name = "compassion.project"
    _inherit = ['compassion.project', 'compassion.mapped.model']

    @api.multi
    def get_location_json(self, multi=False):
        """
        Called by HUB when data is needed for a tile
        :param multi: used to change the wrapper if needed
        :return: dictionary with JSON data of the children
        """
        if not self:
            return {}
        # Location is only supported for one child (we take the first if
        # we have many children)
        data = self[:1].data_to_json("mobile_app_project")
        return data

    @api.multi
    def get_weather_json(self, multi=False):
        if not self:
            return {}
        self.update_weather()
        mapping = {
            'Clear': 'Clear',
            'Clouds': 'Clouds',
            'Rain': 'Rainy',
            'Storm': 'Storm',
            'Mist': 'Clouds',
            'Thunderstorm': 'Storm',
            'Haze': 'Clouds',
            'Drizzle': 'Clouds',
            'Snow': 'Rainy',
            'Smoke': 'Clouds',
            'Dust': 'Clouds',
            'Fog': 'Clouds',
            'Sand': 'Storm',
            'Ash': 'Storm',
            'Squall': 'Storm',
            'Tornado': 'Storm',
        }
        return {
            'ChildWeather': mapping[self.current_weather],
            'ChildTemperature': self.current_temperature,
            # the following fields are not used but prevent app crashes
            'UserWeather': mapping[self.current_weather],
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
        if len(self) == 1:
            data = self.data_to_json("mobile_app_project")
        else:
            data = []
            for child in self:
                data.append(child.data_to_json("mobile_app_project"))
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

        if project:
            result['ProjectServiceResult']['ICPResponseList'] = [(
                project.data_to_json("mobile_app_project"))]
        return result

    def _get_required_param(self, key, params):
        if key not in params:
            raise ValueError('Required parameter {}'.format(key))
        return params[key]

    @api.multi
    def data_to_json(self, mapping_name=None):
        res = super().data_to_json(mapping_name)
        if not res:
            res = {}
        for key, value in list(res.items()):
            if not value:
                res[key] = None
        return res
