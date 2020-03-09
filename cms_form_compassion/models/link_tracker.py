##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from urllib.parse import urljoin

from odoo import models, api


class LinkTracker(models.AbstractModel):
    _inherit = "link.tracker"

    @api.depends("code")
    def _compute_short_url(self):
        """
        Replace web.base.url with web.external.url
        :return:
        """
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.external.url")
        for link in self:
            link.short_url = urljoin(base_url, f"/r/{link.code}")
