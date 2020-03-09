##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models


class PhoneCommon(models.AbstractModel):
    _inherit = "phone.common"

    @api.model
    def click2dial(self, erp_number):
        # Redirect to log call wizard after call from communication
        res = super().click2dial(erp_number)
        if self.env.context.get("click2dial_model") == "partner.communication.job":
            res["action_model"] = "partner.communication.call.wizard"
        return res
