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

logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):

    _name = "product.template"
    _inherit = ["product.template", "compassion.mapped.model"]

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

        mapping = self.env['compassion_mapping'].search([
            'name', '=', "mobile_app_donation"
        ])
        for donation in donation_types:
            result.append(mapping.get_connect_data(donation))

        return result

    @api.multi
    def data_to_json(self, mapping_name=None):
        res = super().data_to_json(mapping_name)
        for key, value in list(res.items()):
            if not value:
                del res[key]
        return res


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
                'FundType': self[:1].default_code,
                'FundId': self[:1].product_tmpl_id.id
            }
        }
