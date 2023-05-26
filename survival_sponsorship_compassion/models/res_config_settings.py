from odoo import api, models, fields


class StaffNotificationSettings(models.TransientModel):
    """ Settings configuration for warning notifications"""

    _inherit = "res.config.settings"

    survival_sponsorship_warn_user_ids = fields.Many2many(
        "res.partner",
        string="Survival sponsorship product places owner",
        domain=[("user_ids", "!=", False), ("user_ids.share", "=", False)],
        readonly=False,
    )

    @api.multi
    def set_values(self):
        super().set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "survival_sponsorship_compassion.survival_sponsorship_warn_user_ids",
            ",".join(list(map(str, self.survival_sponsorship_warn_user_ids.ids))),
        )

    @api.multi
    def get_values(self):
        param_obj = self.env["ir.config_parameter"].sudo()
        res = super().get_values()
        res["survival_sponsorship_warn_user_ids"] = False
        partners = param_obj.get_param(
            "survival_sponsorship_compassion.survival_sponsorship_warn_user_ids", False
        )
        if partners:
            res["survival_sponsorship_warn_user_ids"] = [
                (6, 0, list(map(int, partners.split(","))))
            ]
        return res
