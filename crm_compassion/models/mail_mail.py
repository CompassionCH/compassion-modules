##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class Partner(models.Model):
    _inherit = "mail.mail"

    is_from_employee = fields.Boolean(default=False)
    direction = fields.Selection(
        [
            ("in", "Incoming"),
            ("out", "Outgoing"),
        ]
    )
