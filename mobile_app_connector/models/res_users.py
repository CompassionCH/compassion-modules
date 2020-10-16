##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import models, api, _

logger = logging.getLogger(__name__)


class CompassionLogin(models.Model):
    _name = "res.users"
    _inherit = ["res.users", "compassion.mapped.model"]

    @api.multi
    def data_to_json(self, mapping_name=None):
        res = super().data_to_json(mapping_name)
        if not res:
            res = {}
        if not self:
            res["error"] = _("Wrong user or password")
        else:
            res["login_count"] = len(self.log_ids)
        for key, value in list(res.items()):
            if not value:
                res[key] = None
            else:
                res[key] = str(value)
        return res
