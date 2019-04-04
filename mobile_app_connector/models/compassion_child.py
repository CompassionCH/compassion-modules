# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import models, api
from ..mappings.compassion_child_mapping import MobileChildMapping


logger = logging.getLogger(__name__)


class CompassionChild(models.Model):
    """ A sponsored child """
    _inherit = 'compassion.child'

    @api.multi
    def get_app_json(self, multi=False):
        """
        Called by HUB when data is needed for a tile
        :param multi: used to change the wrapper if needed
        :return: dictionary with JSON data of the children
        """
        if not self:
            return {}
        mapping = MobileChildMapping(self.env)
        wrapper = 'Children' if multi else 'Child'
        if len(self) == 1:
            data = mapping.get_connect_data(self)
        else:
            data = []
            for child in self:
                data.append(mapping.get_connect_data(child))
        return {wrapper: data}

    @api.model
    def mobile_sponsor_children(self, **other_params):
        """
        Mobile app method:
        Returns the sponsored child list for a given sponsor.
        :param userid: the ref of the sponsor
        :param other_params: all request parameters
        :return: JSON list of sponsor children data
        """
        result = []
        partner_ref = self._get_required_param('userid', other_params)

        sponsor = self.env['res.partner'].search([
            # TODO change filter, we can directly search for connected user
            ('ref', '=', partner_ref),
        ], limit=1)
        children = self.search([
            ('partner_id', '=', sponsor.id)
        ])

        mapping = MobileChildMapping(self.env)
        for child in children:
            result.append(mapping.get_connect_data(child))
        return result

    @api.model
    def mobile_get_child_bio(self, **other_params):
        values = dict(other_params)
        child = self.env['compassion.child'].search([
            ('global_id', '=', str(values['child_global_id']))
        ])

        childbio = {
            'name': child.name,
            'firstName': child.firstname,
            'lastName': child.lastname,
            'gender': child.gender,
            'birthdate': child.birthdate,
            'age': child.age,
            'weight': child.weight,
            'height': child.height,
            'educationLevel': child.education_level,
            'academicPerformance': child.academic_performance,
            'vocationalTrainingType': child.vocational_training_type,
            'sponsorshipStatus': child.sponsorship_status
        }

        result = {
            'ChildBioServiceResult': childbio
        }
        return result

    def _get_required_param(self, key, params):
        if key not in params:
            raise ValueError('Required parameter {}'.format(key))
        return params[key]
