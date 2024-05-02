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

    mobile_app = fields.Boolean("Show in Mobile App", index=True, copy=False)
    image_icon = fields.Char(
        "Icon Mobile App", help="See https://fontawesome.com to find code icon."
    )

    @api.model
    def mobile_donation_type(self, **params):
        """
        Mobile app method:
        Returns the list of donation type
        :param other_params: all request parameters
        :return: JSON list of donation type
        """

        result = []
        donation_types = self.sudo().search([("mobile_app", "=", True)])

        for donation in donation_types:
            result.append(donation.data_to_json("mobile_app_donation"))

        return result

    def data_to_json(self, mapping_name=None):
        res = super().data_to_json(mapping_name)
        if not res:
            res = {}
        for key, value in list(res.items()):
            if not value:
                res[key] = None
        return res


class Product(models.Model):

    _inherit = "product.product"

    def get_app_json(self, multi=False):
        """
        Called by HUB when data is needed for a tile
        :param multi: used to change the wrapper if needed
        :return: dictionary with JSON data of the children
        """
        if not self:
            return {}
        return {
            "Appeal": {
                "FundType": self[:1].default_code,
                "FundId": self[:1].product_tmpl_id.id,
            }
        }
