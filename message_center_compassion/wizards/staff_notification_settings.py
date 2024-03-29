##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class StaffNotificationSettings(models.TransientModel):
    """ Settings configuration for any Notifications."""

    _inherit = "res.config.settings"

    # Users to notify for translating GMC values
    translate_notify_ids = fields.Many2many(
        "res.users",
        string="Translate missing GMC values",
        domain=[("share", "=", False)],
        compute="compute_relation_translate_notify_ids",
        inverse="_inverse_relation_translate_notify_ids",
        readonly=False,
    )

    def compute_relation_translate_notify_ids(self):
        self.translate_notify_ids = self._get_translate_notify_ids()

    @api.model
    def _get_translate_notify_ids(self):
        param_obj = self.env["ir.config_parameter"].sudo()
        partners = param_obj.get_param(
            "message_center_compassion.translate_notify_ids", False)
        if partners:
            return [(6, 0, list(map(int, partners.split(","))))]
        else:
            return False

    def _inverse_relation_translate_notify_ids(self):
        self.env["ir.config_parameter"].set_param(
            "message_center_compassion.translate_notify_ids",
            ",".join(map(str, self.translate_notify_ids.ids)),
        )

    @api.model
    def get_values(self):
        res = super().get_values()
        res["translate_notify_ids"] = self._get_translate_notify_ids()
        return res

    @api.model
    def get_param(self, param):
        """Get a single param from ['res.config.settings']"""
        return self.sudo().get_values().get(param)
