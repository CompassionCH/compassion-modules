##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
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
    def related_action_s2b(self):
        action = {
            "name": _("Correspondence Generator"),
            "type": "ir.actions.act_window",
            "res_model": "correspondence.s2b.generator",
            "res_id": self.record_ids,
            "view_type": "form",
            "view_mode": "form",
        }
        return action

    @api.multi
    def related_action_s2b_imports(self):
        action = {
            "name": _("Correspondence Import"),
            "type": "ir.actions.act_window",
            "res_model": "import.letters.history",
            "res_id": self.record_ids,
            "view_type": "form",
            "view_mode": "form",
        }
        return action
