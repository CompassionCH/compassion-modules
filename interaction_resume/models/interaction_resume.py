##############################################################################
#
#    Copyright (C) 2024 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, fields, models


class InteractionResume(models.Model):
    _inherit = "translatable.model"
    _name = "interaction.resume"
    _description = "Resume of a given partner"
    _order = "date desc"
    _rec_name = "subject"

    partner_id = fields.Many2one(
        "res.partner", "Partner", required=True, index=True, ondelete="cascade"
    )
    email = fields.Char()
    communication_type = fields.Selection(
        [
            ("Paper", "Paper"),
            ("Phone", "Phone"),
            ("SMS", "SMS"),
            ("Email", "Email"),
            ("Mass", "Mass Mailing"),
            ("Other", "Other"),
            ("Support", "Support"),
        ]
    )
    direction = fields.Selection(
        [
            ("in", "Incoming"),
            ("out", "Outgoing"),
        ]
    )
    date = fields.Datetime()
    subject = fields.Text()
    other_type = fields.Char()
    has_attachment = fields.Boolean()
    body = fields.Text()
    res_model = fields.Char(required=True, index=True)
    res_id = fields.Integer(required=True, index=True)
    tracking_status = fields.Selection(
        [
            ("error", "Error"),
            ("deferred", "Deferred"),
            ("sent", "Sent"),
            ("delivered", "Delivered"),
            ("opened", "Opened"),
            ("rejected", "Rejected"),
            ("spam", "Spam"),
            ("unsub", "Unsubscribed"),
            ("bounced", "Bounced"),
            ("soft-bounced", "Soft bounced"),
            ("canceled", "Canceled"),
            ("outgoing", "Outgoing"),
            ("exception", "Exception"),
            ("replied", "Replied"),
            ("ignored", "Ignored"),
        ]
    )

    def open_related_action(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self.res_model,
            "res_id": self.res_id,
            "view_mode": "form",
            "target": "current",
            "name": self.subject or self.communication_type,
        }

    def refresh(self):
        partner = self.mapped("partner_id")[:1]
        partner.fetch_interactions()
        return True

    def fetch_more(self):
        partner = self.mapped("partner_id")[:1]
        partner.fetch_interactions(page=partner.last_interaction_fetch_page + 1)
        return True

    @api.model_create_multi
    def create(self, vals_list):
        # Avoid duplicates
        res = self.env[self._name]
        for vals in vals_list:
            existing_interaction = self.search(
                [
                    ("partner_id", "=", vals["partner_id"]),
                    ("direction", "=", vals["direction"]),
                    ("date", "=", vals["date"]),
                ]
            )
            if not existing_interaction:
                existing_interaction = super().create(vals)
            res += existing_interaction
        return res
