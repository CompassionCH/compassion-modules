##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Noé Berdoz <nberdoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class SdsSubFollowers(models.Model):
    """Configuration for SUB sponsorship Notifications."""

    _name = "sds.sub.followers"
    _description = "SDS SUB Sponsorship Followers"
    _order = "sequence,id"

    # User to notify after Child Departure
    user_id = fields.Many2one(
        "res.users",
        string="Sub sponsorships follower",
        domain=[("share", "=", False)],
        required=True,
    )
    # Language that could have notifications
    res_lang_id = fields.Many2one(
        "res.lang",
        string="Active language",
        domain=[("active", "=", True)],
        help="Language for which to be notified (empty for all languages)",
    )
    sequence = fields.Integer(
        default=10,
        required=True,
        help="When multiple followers match, the one with highest priority"
        "(at the top) will be assigned.",
    )

    _sql_constraints = [
        (
            "unique_user",
            "unique(user_id,res_lang_id)",
            "This user is already configured.",
        )
    ]
