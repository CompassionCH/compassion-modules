from odoo import models


class GmcMessagePoolProcess(models.TransientModel):
    _name = "gmc.message.process"
    _description = "GMC Pool Process Wizard"

    def process_messages(self):
        active_ids = self.env.context.get("active_ids", [])
        self.env["gmc.message"].browse(active_ids).process_messages()
        action = {
            "name": "Message treated",
            "type": "ir.actions.act_window",
            "view_mode": "list,form",
            "res_model": "gmc.message",
            "domain": [("id", "in", active_ids)],
            "target": "current",
        }

        return action
