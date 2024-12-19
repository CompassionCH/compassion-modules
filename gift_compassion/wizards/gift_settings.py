##############################################################################
#
#    Copyright (C) 2016-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class GiftNotificationSettings(models.TransientModel):
    """Settings configuration for Gift Notifications."""

    _inherit = "res.config.settings"

    # Users to notify
    gift_notify_ids = fields.Many2many(
        "res.partner",
        string="Gift Undeliverable",
        domain=[
            ("user_ids", "!=", False),
            ("user_ids.share", "=", False),
        ],
        compute="_compute_gift_notify_ids",
        inverse="_inverse_gift_notify_ids",
    )

    def _compute_gift_notify_ids(self):
        for rec in self:
            rec.gift_notify_ids = self._get_gift_notify_ids()

    def _inverse_gift_notify_ids(self):
        self.env["ir.config_parameter"].set_param(
            "gift_compassion.gift_notify_ids",
            ",".join(map(str, self.gift_notify_ids.ids)),
        )

    def get_values(self):
        res = super().get_values()
        res.update(
            {
                "gift_notify_ids": self._get_gift_notify_ids(),
            }
        )
        return res

    def _get_gift_notify_ids(self):
        partners = self.env["ir.config_parameter"].get_param(
            "gift_compassion.gift_notify_ids", False
        )
        if partners:
            return [(6, 0, list(map(int, partners.split(","))))]
        else:
            return False
