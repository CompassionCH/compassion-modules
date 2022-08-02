##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, _
from odoo.tools.safe_eval import safe_eval


class QueueJob(models.Model):
    _inherit = "queue.job"

    def related_action_automation(self):
        records = self.record_ids
        model = "ir.actions.server"
        if self.result:
            records = safe_eval(self.result.split("job")[1])
            model = "partner.communication.job"
        action = {
            "name": _("Automation"),
            "type": "ir.actions.act_window",
            "res_model": model,
            "domain": [("id", "in", records)],
            "view_type": "form",
            "view_mode": "tree,form",
        }
        return action
