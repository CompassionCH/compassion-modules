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
from ..mappings.from_letter_mapping import FromLetterMapping


logger = logging.getLogger(__name__)


class CompassionChild(models.Model):
    """ A sponsored child """
    _inherit = 'compassion.child'

    @api.model
    def mobile_sponsor_children(self, userid=None, **other_params):
        """
        Mobile app method:
        Returns the sponsored child list for a given sponsor.
        :param userid: the ref of the sponsor
        :param other_params: all request parameters
        :return: JSON list of sponsor children data
        """
        result = []
        if userid is None:
            return result

        sponsor = self.env['res.partner'].search([
            # TODO add filter only portal users
            ('ref', '=', userid),
        ], limit=1)
        children = self.search([
            ('sponsor_id', '=', sponsor.id)
        ])

        mapping = MobileChildMapping(self.env)
        for child in children:
            result.append(mapping.get_connect_data(child))
        return result

    @api.model
    def mobile_get_letters(self, userid=None, **other_params):
        """
        Mobile app method:
        Returns the letters letters from a Child
        :param needid: beneficiary id
        :param supgrpid: child id
        """
        partner_id = self._get_required_param('supgrpid', other_params)
        child_id = self._get_required_param('needid', other_params)
        letters = self.env['correspondence'].search([
            ('partner_id', '=', partner_id),
            ('child_id', '=', child_id),
            # todo, check if needed
            ('direction', '=', 'Beneficiary To Supporter')
        ])

        mapper = FromLetterMapping(self.env)
        return [mapper.get_connect_data(letter) for letter in letters]

    def _get_required_param(self, key, params):
        if key not in params:
            raise ValueError('Required parameter {}'.format(key))