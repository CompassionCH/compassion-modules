##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Jonathan Tarabbia
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import models, api

logger = logging.getLogger(__name__)


class CompassionRecurringContract(models.Model):
    """ A sponsorship """

    _inherit = "recurring.contract"

    def get_app_json(self, multi=False):
        """
        Called by HUB when data is needed for a tile related a sponsorship row
        :param multi: used to change the wrapper if needed
        :return: dictionary with JSON data of the children
        """
        child = self.sudo().mapped("child_id")
        return child.get_app_json(multi)

    @api.model
    def create(self, vals):
        contract = super().create(vals)
        sponsors = self.mapped("partner_id") + self.mapped("correspondent_id")
        sponsors.mapped("app_messages").write({
            "force_refresh": True
        })
        return contract

    def contract_active(self):
        sponsors = self.mapped("partner_id") + self.mapped("correspondent_id")
        sponsors.mapped("app_messages").write({
            "force_refresh": True
        })
        return super().contract_active()
