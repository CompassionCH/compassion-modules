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
        readonly=False,
        domain="[('model_id', '=', model_id)]",
    )
    partner_field = fields.Char("Partner field name", help="'self' for record itself")
    send_mode = fields.Selection("send_mode_select")
    auto_send = fields.Boolean()

    def send_mode_select(self):
        return self.env["partner.communication.job"].send_mode_select()

    @api.model
    def _run_action_communication(self, action, eval_context=None):
        if (
            not action.config_id
            or not self._context.get("active_id")
            or self._is_recompute(action)
        ):
            return False

        model_name = action.model_name
        if "records" in eval_context:
            for raw_record in eval_context["records"]:
                is_self = action.partner_field == "self"
                partner = raw_record if is_self else raw_record[action.partner_field]
                children = eval_context["records"]
                records = self.env[model_name].search(
                    [
                        (action.partner_field, "=", partner.id),
                        ("id", "in", children.ids),
                    ]
                )
                # Use same job if possible to group communications for one partner
                existing_job = self.env["queue.job"].search(
                    [
                        ("state", "=", "pending"),
                        ("method_name", "=", "create_communication_job"),
                        ("model_name", "=", self._name),
                        ("func_string", "like", f"'partner_id': {partner.id}"),
                        ("func_string", "like", f"'config_id': {action.config_id.id}"),
                    ]
                )
                if existing_job:
                    vals = existing_job.args[0]
                    vals["object_ids"].extend(records.ids)
                    existing_job.unlink()
                else:
                    vals = {
                        "partner_id": partner.id,
                        "object_ids": records.ids,
                        "config_id": action.config_id.id,
                    }
                if self.send_mode:
                    vals["send_mode"] = self.send_mode
                if self.auto_send:
                    vals["auto_send"] = self.auto_send
                delay = datetime.now() + timedelta(minutes=3)
                self.with_delay(eta=delay).create_communication_job(vals)
        return True

    def create_communication_job(self, vals):
        return self.env["partner.communication.job"].create(vals)
