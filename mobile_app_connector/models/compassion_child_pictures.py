##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import datetime
import logging

from odoo import models, api

logger = logging.getLogger(__name__)


class CompassionChildPictures(models.Model):
    """ A sponsored child """

    _name = "compassion.child.pictures"
    _inherit = ["compassion.child.pictures", "compassion.mapped.model"]

    @property
    def image_url_compassion(self, type="fullshot"):
        if type.lower() not in ["headshot", "fullshot"]:
            raise ValueError("Expected argument 'type' to be 'headshot' or 'fullshot'")

        base_url = self.env["ir.config_parameter"].sudo().get_param("web.external.url")
        endpoint = base_url + "/web/image/compassion.child.pictures"
        return f"{endpoint}/{self.id}/{type}/" f"{self.date}_{self.child_id.id}.jpg"

    @api.multi
    def get_app_json(self, multi=False):
        """
        Called by HUB when data is needed for a tile
        :param multi: used to change the wrapper if needed
        :return: dictionary with JSON data of the children
        """
        if not self:
            return {}
        # wrapper = 'Images' if multi else 'Images'
        if len(self) == 1:
            data = [self.data_to_json("mobile_app_child_pictures")]
        else:
            data = []
            for child in self:
                data.append(child.data_to_json("mobile_app_child_pictures"))
        return data

    @api.multi
    def data_to_json(self, mapping_name=None):
        res = super().data_to_json(mapping_name)
        if not res:
            res = {}
        res["Date"] = datetime.datetime.strptime(res["Date"], "%Y-%m-%d").strftime(
            "%d-%m-%Y %H:%M:%S"
        )

        return res
