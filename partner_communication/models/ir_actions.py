##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import datetime, timedelta

from odoo import api, fields, models


class IrActionsServer(models.Model):
    _inherit = "ir.actions.server"

    state = fields.Selection(
        selection_add=[("communication", "Send Communication")],
        ondelete={"communication": "cascade"},
    )
    config_id = fields.Many2one(
        "partner.communication.config",
        "Communication type",
        domain="[('model_id', '=', model_id)]",
    )
    partner_field = fields.Char("Partner field name", help="'self' for record itself")
    send_mode = fields.Selection("send_mode_select")
    auto_send = fields.Boolean()

    def send_mode_select(self):
        return self.env["partner.communication.job"].send_mode_select()

    @api.model
    def _run_action_communication(self, eval_context=None):
        if (
            not self.config_id
            or not self._context.get("active_id")
            or self._is_recompute()
        ):
            return False

        model_name = self.model_name
        records_to_process = eval_context.get("records")
        if records_to_process:
            is_self = self.partner_field == "self"
            # Group records by partner to avoid redundant processing and duplicate jobs
            partner_map = {}
            for rec in records_to_process:
                partner = rec if is_self else rec[self.partner_field]
                partner_map.setdefault(partner, self.env[model_name])
                partner_map[partner] |= rec

            for partner, records in partner_map.items():
                vals = {
                    "partner_id": partner.id,
                    "object_ids": records.ids,
                    "config_id": self.config_id.id,
                }
                if self.send_mode:
                    vals["send_mode"] = self.send_mode
                if self.auto_send:
                    vals["auto_send"] = self.auto_send
                delay = datetime.now() + timedelta(minutes=3)
                identity_key = f"create_communication.{self.config_id.id}.{partner.id}"
                self.with_delay_sh(
                    "create_communication_job",
                    vals,
                    identity_key=identity_key,
                    eta=delay,
                    fresh_context=True,
                )
        return {}

    def create_communication_job(self, vals):
        """Automated communication creation"""
        return self.env["partner.communication.job"].create(vals)
