##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Noé Berdoz <nberdoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class SdsSubFollowers(models.Model):
    """Configuration for SUB sponsorship Notifications."""
    _name = 'sds.sub.followers'
    _description = 'SDS SUB Sponsorship Followers'

    # User to notify after Child Departure
    user_id = fields.Many2one(
        "res.users",
        string="Sub sponsorships follower",
        domain=[("share", "=", False)],
    )

    # Language that could have notifications
    res_lang_id = fields.Many2one(
        "res.lang",
        string="Active languages",
        domain=[("active", "=", True)],
    )
