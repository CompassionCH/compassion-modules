# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nathan Fluckiger <nathan.fluckiger@hotmail.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging


from odoo import models, api
from ..mappings.compassion_donation_mapping import MobileDonationMapping

logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):

    _inherit = "product.template"

    @api.model
    def mobile_donation_type(self, **other_params):
        """
        Mobile app method:
        Returns the list of donation type
        :param userid: the ref of the sponsor
        :param other_params: all request parameters
        :return: JSON list of donation type
        """

        result = []

        donationtypes = self.search([('categ_id', '=', 'Fund')])

        mapping = MobileDonationMapping(self.env)
        for donation in donationtypes:
            result.append(mapping.get_connect_data(donation))

        return result
