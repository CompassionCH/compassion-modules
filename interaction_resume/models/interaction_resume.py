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
    user_id = fields.Many2one("res.users", "User", required=False, index=True)
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

    def action_refresh(self):
        self.mapped("partner_id")[:1].refresh_interactions()
        return True

    def fetch_more(self):
        partner = self.mapped("partner_id")[:1]
        partner.fetch_interactions(page=partner.last_interaction_fetch_page + 1)
        return True

    def _identity_of(self, vals):
        """What tells one entry of a resume from another."""
        source = self.env[vals["res_model"]]
        return (
            vals.get("partner_id") or False,
            source._name,
            vals.get("res_id") or False,
        ) + source._interaction_discriminator(vals)

    def _identity(self):
        self.ensure_one()
        return self._identity_of(
            {
                "partner_id": self.partner_id.id,
                "res_model": self.res_model,
                "res_id": self.res_id,
                "date": self.date,
                "subject": self.subject,
            }
        )

    def _update_from_source(self, vals):
        self.ensure_one()
        changed = {
            field: value
            for field, value in vals.items()
            if self._fields[field].convert_to_write(self[field], self) != value
        }
        if changed:
            self.write(changed)
        return self

    @api.model_create_multi
    def create(self, vals_list):
        if not vals_list:
            return self.browse()
        partners = {vals.get("partner_id") for vals in vals_list}
        res_models = {vals.get("res_model") for vals in vals_list}
        listed = {
            entry._identity(): entry
            for entry in self.search(
                [
                    ("partner_id", "in", list(partners)),
                    ("res_model", "in", list(res_models)),
                ]
            )
        }
        res = self.browse()
        to_create = []
        for vals in vals_list:
            identity = self._identity_of(vals)
            entry = listed.get(identity)
            if entry:
                res += entry._update_from_source(vals)
            elif identity not in listed:
                # Mark it as taken, so that a duplicate later in the same
                # batch does not create a second entry for it.
                listed[identity] = None
                to_create.append(vals)
        return res + super().create(to_create)
