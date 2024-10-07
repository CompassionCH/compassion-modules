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
    gift_expense_account_id = fields.Many2one(
        "account.account",
        "Gift expense account",
    )
    gift_income_account_id = fields.Many2one(
        "account.account",
        "Payable gift account",
    )
    gift_analytic_id = fields.Many2one(
        "account.analytic.account",
        "Gift analytic account",
        config_parameter="gift_compassion.analytic_id",
    )
    gift_analytic_tag_id = fields.Many2one(
        "account.analytic.tag",
        "Gift analytic tag",
        config_parameter="gift_compassion.analytic_tag_id",
    )
    gift_journal_id = fields.Many2one(
        "account.journal",
        "Gift journal id",
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
        param_obj = self.env["ir.config_parameter"]
        company_id = self.env.company.id
        res.update(
            {
                "gift_notify_ids": self._get_gift_notify_ids(),
                "gift_expense_account_id": int(
                    param_obj.get_param(
                        f"gift_compassion.gift_expense_account_{company_id}"
                    )
                    or 0
                ),
                "gift_income_account_id": int(
                    param_obj.get_param(
                        f"gift_compassion.gift_income_account_{company_id}"
                    )
                    or 0
                ),
                "gift_journal_id": int(
                    param_obj.get_param(f"gift_compassion.gift_journal_id{company_id}")
                    or 0
                ),
            }
        )
        return res

    def set_values(self):
        company_id = self.env.company.id
        self.env["ir.config_parameter"].set_param(
            f"gift_compassion.gift_expense_account_{company_id}",
            str(self.gift_expense_account_id.id or 0),
        )
        self.env["ir.config_parameter"].set_param(
            f"gift_compassion.gift_income_account_{company_id}",
            str(self.gift_income_account_id.id or 0),
        )
        self.env["ir.config_parameter"].set_param(
            f"gift_compassion.gift_journal_id{company_id}",
            str(self.gift_journal_id.id or 0),
        )
        super().set_values()

    def _get_gift_notify_ids(self):
        partners = self.env["ir.config_parameter"].get_param(
            "gift_compassion.gift_notify_ids", False
        )
        if partners:
            return [(6, 0, list(map(int, partners.split(","))))]
        else:
            return False
