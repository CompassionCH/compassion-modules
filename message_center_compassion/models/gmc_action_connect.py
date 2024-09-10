##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import _, fields, models


class GmcActionConnect(models.Model):
    """
    Maps an Action with a Connect Message Type
    """

    _name = "gmc.action.connect"
    _description = "GMC Action Connect"
    _rec_name = "connect_schema"

    connect_schema = fields.Char(required=True)
    action_id = fields.Many2one(
        "gmc.action", "GMC Action", required=False, readonly=False
    )
    ignored = fields.Boolean(
        help="True if the received connect_schema should be ignored"
    )

    _sql_constraints = [
        (
            "connect_schema_uniq",
            "UNIQUE(connect_schema)",
            _("You cannot have two actions with same connect schema."),
        )
    ]
