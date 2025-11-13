##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class SBCSettings(models.TransientModel):
    """Settings configuration for any Notifications."""

    _inherit = "res.config.settings"

    # Users to notify after Child Departure
    letter_responsible = fields.Many2one(
        "res.users",
        string="Letter translation check unsuccessful",
        domain=[("share", "=", False)],
        readonly=False,
        config_parameter="sbc_compassion.letter_responsible",
    )
