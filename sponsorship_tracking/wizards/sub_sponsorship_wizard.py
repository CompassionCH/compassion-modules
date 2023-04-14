##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo.addons.child_compassion.models.compassion_hold import HoldType

from odoo import api, models, fields, _


class SubSponsorshipWizard(models.TransientModel):
    _name = "sds.subsponsorship.wizard"
    _description = "Sub Sponsorship Wizard"

    state = fields.Selection([("sub", "sub"), ("no_sub", "no_sub")])
    channel = fields.Selection(
        [("childpool", "Global Childpool"), ("direct", "Direct")]
    )
    child_id = fields.Many2one(
        "compassion.child",
        "Child",
        domain=[("state", "in", ["N", "I"])],
        readonly=False,
    )
    no_sub_default_reasons = fields.Many2one(
        "recurring.contract.end.reason", "No sub reason"
    )
    is_other = fields.Boolean(compute="_compute_is_other")
    no_sub_reason = fields.Char("Precisions")

    @api.depends("no_sub_default_reasons")
    def _compute_is_other(self):
        other = self.env.ref("sponsorship_compassion.end_reason_other")
        for record in self:
            record.is_other = record.no_sub_default_reasons == other

    def create_subsponsorship(self):
        """Creates a subsponsorship."""
        self.ensure_one()

        sponsorship_id = self.env.context.get("active_id")
        contract_obj = self.env["recurring.contract"]
        contract = contract_obj.browse(sponsorship_id)
        contract.sds_uid = self.env.user
        sub_contract = contract.copy(
            {
                "parent_id": sponsorship_id,
                "channel": "sub",
                "child_id": self.child_id.id,
                "user_id": False,
                "sds_uid": self.env.uid,
                "medium_id": self.env.ref("utm.utm_medium_direct").id,
                "source_id": self.env.ref("sponsorship_compassion.utm_source_sub").id,
                "campaign_id": self.env.ref(
                    "sponsorship_compassion.utm_campaign_sub"
                ).id,
            }
        )
        today = datetime.today()
        if contract.last_paid_invoice_date:
            sub_invoice_date = contract.last_paid_invoice_date + relativedelta(months=1)

        if self.child_id:
            return {
                "name": sub_contract.name,
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "recurring.contract",
                "res_id": sub_contract.id,
                "target": "current",
                "context": self.with_context(
                    {
                        "default_type": "S",
                    }
                ).env.context,
            }
        else:
            return {
                "name": _("Global Childpool"),
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "compassion.childpool.search",
                "target": "current",
                "context": self.with_context(
                    {
                        "default_take": 1,
                        "contract_id": sub_contract.id,
                        "default_type": HoldType.SUB_CHILD_HOLD.value,
                        "default_channel": "sub",
                        "default_return_action": "sub",
                        "default_source_code": "sub_proposal",
                    }
                ).env.context,
            }

    def no_sub(self):
        """No SUB for the sponsorship."""
        self.ensure_one()
        sponsorship_id = self.env.context.get("active_id")
        contract = self.env["recurring.contract"].browse(sponsorship_id)
        reason = self.no_sub_default_reasons.name
        if reason.lower() == "other":
            reason = self.no_sub_reason
        contract.write(
            {
                "no_sub_reason": reason,
                "sds_uid": self.env.uid,
                "sds_state": "no_sub",
                "color": 1,
            }
        )
        contract.partner_id.message_post(
            subject=_("%s - No SUB") % contract.child_code,
            body=_("The sponsor doesn't want a new child."),
        )
        return True
