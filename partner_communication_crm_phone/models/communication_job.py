##############################################################################
#
#    Copyright (C) 2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import _, fields, models


class CommunicationJob(models.Model):
    _inherit = "partner.communication.job"

    phonecall_id = fields.Many2one("crm.phonecall", "Phonecall log", readonly=True)

    def log_call(self):
        return {
            "name": _("Log your call"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "partner.communication.call.wizard",
            "context": self.with_context(
                {
                    "click2dial_id": self.id,
                    "phone_number": self.partner_id.phone or self.partner_id.mobile,
                    "timestamp": fields.Datetime.now(),
                    "default_communication_id": self.id,
                }
            ).env.context,
            "target": "new",
        }

    def call(self):
        """Call partner from tree view button."""
        self.ensure_one()
        self.env["phone.common"].with_context(
            click2dial_model=self._name, click2dial_id=self.id
        ).click2dial(self.partner_id.phone or self.partner_id.mobile)
        return self.log_call()
