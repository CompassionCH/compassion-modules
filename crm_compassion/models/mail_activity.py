##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Soulaymane Lamrani <soulaymane.lamrani@protonmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, api


class MailActivity(models.Model):
    _inherit = "mail.activity"

    phonecall_id = fields.Many2one("crm.phonecall", "Phonecall")

    @api.model
    def create(self, vals_list):
        """
        Links mail activities on crm.phonecall
        """
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        call_activity_id = self.env.ref("mail.mail_activity_data_call").id
        partner_model_id = self.env.ref("base.model_res_partner").id
        lead_model_id = self.env.ref("crm.model_crm_lead").id
        for vals in vals_list:
            if vals.get("activity_type_id") == call_activity_id:
                phonecall_vals = {
                    "date": vals["date_deadline"],
                    "name": vals.get("summary", "Phonecall"),
                    "user_id": vals["user_id"],
                    "direction": "outbound",
                    "state": "open"
                }
                if vals["res_model_id"] == partner_model_id:
                    phonecall_vals["partner_id"] = vals["res_id"]

                elif vals["res_model_id"] == lead_model_id:
                    phonecall_vals.update({
                        "opportunity_id": vals["res_id"],
                        "partner_id": self.env["crm.lead"].browse(
                            vals["res_id"]).partner_id.id,
                    })
                else:
                    model = self.env["ir.model"].browse(vals["res_model_id"]).model
                    if hasattr(self.env[model], "partner_id"):
                        phonecall_vals["partner_id"] = self.env[model].browse(
                            vals["res_id"]).partner_id.id
                vals["phonecall_id"] = self.env["crm.phonecall"].create(
                    phonecall_vals).id
        return super().create(vals_list)

    def action_feedback(self, feedback=False):
        self.mapped("phonecall_id").write({
            "state": "done"
        })
        return super().action_feedback(feedback)
