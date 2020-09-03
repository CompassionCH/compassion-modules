##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models


class ProjectCompassion(models.Model):
    _inherit = "compassion.project"

    def _hold_letters(self):
        letters = self.env["correspondence"].search(
            [
                ("child_id.code", "like", self.fcp_id),
                ("direction", "=", "Supporter To Beneficiary"),
                ("kit_identifier", "=", False),
            ]
        )
        letters.hold_letters()

    def _reactivate_letters(self):
        letters = self.env["correspondence"].search(
            [
                ("child_id.code", "like", self.fcp_id),
                ("direction", "=", "Supporter To Beneficiary"),
                ("kit_identifier", "=", False),
            ]
        )
        letters.reactivate_letters()
