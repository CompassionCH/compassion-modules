##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
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
    def related_action_sms_request(self):
        action = {
            "name": _("SMS Request"),
            "type": "ir.actions.act_window",
            "res_model": "sms.child.request",
            "res_id": self.record_ids[0],
            "domain": [("id", "in", self.record_ids)],
            "view_type": "form",
            "view_mode": "form",
        }
        return action

    @api.multi
    def related_action_update_partner(self):
        action = {
            "name": _("Partner update"),
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "res_id": self.record_ids[0],
            "domain": [("id", "in", self.record_ids)],
            "view_type": "form",
            "view_mode": "form",
        }
        return action
