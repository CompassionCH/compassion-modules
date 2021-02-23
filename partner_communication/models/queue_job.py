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


class QueueJob(models.Model):
    _inherit = "queue.job"

    @api.multi
    def related_action_automation(self):
        action = {
            "name": _("Automation"),
            "type": "ir.actions.act_window",
            "res_model": "ir.actions.server",
            "domain": [("id", "in", self.record_ids)],
            "view_type": "form",
            "view_mode": "tree,form",
        }
        return action
