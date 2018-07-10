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
            ('partner_id', '=', sponsor.id)
        ])
        mapping = MobileChildMapping(self.env)
        for child in children:
            result.append(mapping.get_connect_data(child))
        return result
