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


from odoo import models, api, fields
from ..mappings.compassion_donation_mapping import MobileDonationMapping

logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):

    _inherit = "product.template"

    mobile_app = fields.Boolean('Show in Mobile App', index=True)
    image_icon = fields.Char('Icon Mobile App',
                             help="See https://fontawesome.com to "
                                  "find code icon.")

    @api.model
    def mobile_donation_type(self, **params):
        """
        Mobile app method:
        Returns the list of donation type
        :param other_params: all request parameters
        :return: JSON list of donation type
        """

        result = []
        donation_types = self.search([('mobile_app', '=', True)])

        mapping = MobileDonationMapping(self.env)
        for donation in donation_types:
            result.append(mapping.get_connect_data(donation))

        return result


class Product(models.Model):

    _inherit = "product.product"

    @api.multi
    def get_app_json(self, multi=False):
        """
        Called by HUB when data is needed for a tile
        :param multi: used to change the wrapper if needed
        :return: dictionary with JSON data of the children
        """
        if not self:
            return {}
        return {
            'Appeal': {
                'FundType': self[:1].default_code
            }
        }
