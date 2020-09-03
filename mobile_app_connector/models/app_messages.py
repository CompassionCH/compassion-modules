##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields

# Time in days after which the hub is reconstructed for fetching any new tiles
HUB_REFRESH_DAYS = 3


class AppMessages(models.Model):
    _name = "mobile.app.messages"

    partner_id = fields.Many2one(
        "res.partner", "Partner", readonly=True, required=True, ondelete="cascade"
    )
    json_messages = fields.Char()
    last_refresh_date = fields.Datetime()
    needs_refresh = fields.Boolean(compute="_compute_needs_refresh")
    is_expired = fields.Boolean(compute="_compute_is_expired")
    force_refresh = fields.Boolean(help="Force the hub of sponsor to refresh")

    @api.multi
    def _compute_needs_refresh(self):
        for hub in self:
            hub.needs_refresh = hub.force_refresh or hub.is_expired

    @api.multi
    def _compute_is_expired(self):
        for hub in self:
            if hub.last_refresh_date:
                refresh_since = fields.Datetime.now() - hub.last_refresh_date
                hub.is_expired = refresh_since.days > HUB_REFRESH_DAYS
            else:
                hub.is_expired = True

    @api.multi
    def write(self, vals):
        # Reset force refresh hub when it is just refreshed.
        if vals.get("last_refresh_date"):
            vals["force_refresh"] = False
        return super().write(vals)
