##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Soulaymane Lamrani <soulaymane.lamrani@protonmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import datetime

from addons import crm
from odoo import models, fields, api


class MailActivity(models.Model):
    _inherit = "mail.activity"

    phonecall_ids = fields.Many2one("crm.phonecall")

    @api.model
    def create(self, vals):
        if "activity_type_id" in vals:
            if vals["activity_type_id"] == \
                    self.env.ref("mail.mail_activity_data_call").id:
                if vals["res_model_id"] == self.env["ir.model"].search([(
                    "model", "=", "res.partner"
                )]).id:
                    vals["phonecall_ids"] = self.env["crm.phonecall"].create({
                        "date": vals["date_deadline"],
                        "name": vals["summary"],
                        "partner_id": vals["res_id"],
                        "user_id": vals["user_id"],
                        "direction": "outbound",
                        "state": "open"
                    }).id

                if vals["res_model_id"] == self.env["ir.model"].search([(
                    "model", "=", "crm.lead"
                )]).id:
                    vals["phonecall_ids"] = self.env["crm.phonecall"].create({
                        "date": vals["date_deadline"],
                        "name": vals["summary"],
                        "opportunity_id": vals["res_id"],
                        "partner_id": self.env["crm.lead"].search([(
                            "id", "=", vals["res_id"]
                        )]).partner_id.id,
                        "user_id": vals["user_id"],
                        "direction": "outbound",
                        "state": "open"
                    }).id
        return super(MailActivity, self.sudo()).create(vals)

    def action_feedback(self, feedback=False):
        phonecall = self.env["crm.phonecall"].search([(
            "id", "=", self.phonecall_ids.id
        )])
        phonecall.write({
            "state": "done"
        })
        return super(MailActivity, self).action_feedback(feedback)
