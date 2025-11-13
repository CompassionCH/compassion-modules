##############################################################################
#
#    Copyright (C) 2020-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import Command, api, fields, models
from odoo.tools import ormcache

from ..tools.onramp_connector import OnrampConnector


class Settings(models.TransientModel):
    """Settings configuration."""

    _inherit = "res.config.settings"

    # Users to notify for translating GMC values
    translate_notify_ids = fields.Many2many(
        "res.users",
        "translate_notify_rel",
        string="Translate missing GMC values",
        domain=[("share", "=", False)],
        compute="_compute_relation_translate_notify_ids",
        inverse="_inverse_relation_translate_notify_ids",
    )
    connect_api_key = fields.Char(
        "Api Key", config_parameter="message_center_compassion.connect_api_key"
    )
    connect_gpid = fields.Char(
        "GP ID", config_parameter="message_center_compassion.connect_gpid"
    )
    connect_gpname = fields.Char(
        "GP Name", config_parameter="message_center_compassion.connect_gpname"
    )
    connect_client = fields.Char(
        "Client", config_parameter="message_center_compassion.connect_client"
    )
    connect_secret = fields.Char(
        "Secret", config_parameter="message_center_compassion.connect_secret"
    )
    delivery_service_api_key = fields.Char(
        config_parameter="message_center_compassion.delivery_service_api_key"
    )
    delivery_service_status = fields.Boolean(
        string="GMC Queue active",
        compute="_compute_delivery_status",
        inverse="_inverse_delivery_status",
        help="Returns the egress status of Onramp (CI). "
        "True indicates that CI OnRamp is enabled to make REST calls to the GP OnRamp. "
        "False indicates that CI OnRamp will queue messages,"
        "and will NOT make REST calls to the GP OnRamp.",
    )

    @api.depends("connect_gpid", "delivery_service_api_key")
    def _compute_delivery_status(self):
        connector = OnrampConnector(self.env)
        if not connector._connect_url or not self.delivery_service_api_key:
            return
        connector.patch_session("api_key", self.delivery_service_api_key)
        gpid = self.connect_gpid.lower()
        result = connector.send_message(f"delivery-service-{gpid}/egressControl", "GET")
        connector.patch_session("api_key", self.connect_api_key)
        if isinstance(result, dict) and "content" in result:
            if isinstance(result["content"], dict):
                self.delivery_service_status = (
                    result["content"].get("enabled", "true") == "true"
                )
                return
        self.delivery_service_status = True

    def _inverse_delivery_status(self):
        connector = OnrampConnector(self.env)
        gpid = self.connect_gpid.lower()
        if not connector._connect_url or not self.delivery_service_status:
            return
        connector.patch_session("api_key", self.delivery_service_api_key)
        connector.send_message(
            f"delivery-service-{gpid}/egressControl",
            "PUT",
            params={"EgressEnabled": self.delivery_service_status},
        )
        connector.patch_session("api_key", self.connect_api_key)

    def _compute_relation_translate_notify_ids(self):
        self.translate_notify_ids = self._get_translate_notify_ids()

    @api.model
    def _get_translate_notify_ids(self):
        param_obj = self.env["ir.config_parameter"].sudo()
        partners = param_obj.get_param(
            "message_center_compassion.translate_notify_ids", False
        )
        if partners:
            return [Command.set(list(map(int, partners.split(","))))]
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

    @ormcache("param", "self.env.company.id")
    @api.model
    def get_param(self, param, default=None):
        """Get a single param from ['res.config.settings']"""
        return self.sudo().default_get([param]).get(param, default)
