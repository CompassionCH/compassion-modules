##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Praz <npraz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class CrmStage(models.Model):
    _inherit = "crm.stage"

    is_lost = fields.Boolean("Is Lost Stage?", default=False)

    _sql_constraints = [
        (
            "cannot_be_lost_and_won",
            "CHECK(NOT(is_lost = 'True' AND is_won = 'True'))",
            "Stage cannot be both Lost and Won",
        )
    ]
