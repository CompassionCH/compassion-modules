##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields, _


class ChildHoldWizard(models.TransientModel):
    """ Add return action for sponsoring selected child. """

    _inherit = "child.hold.wizard"

    return_action = fields.Selection(selection_add=[("sponsor", "Sponsor the child")],
                                     ondelete={"sponsor": "set default"})

    def _get_action(self, holds):
        action = super()._get_action(holds)
        if self.return_action == "sponsor":
            child = holds[0].child_id
            action.update(
                {
                    "name": _("Sponsor the child on hold"),
                    "res_model": "recurring.contract",
                    "res_id": self.env.context.get("contract_id"),
                    "view_mode": "form",
                }
            )
            action["context"] = self.with_context(
                {
                    "default_child_id": child.id,
                    "child_id": child.id,
                    "default_type": "S",
                }
            ).env.context
        return action

    def send(self):
        if self.return_action == "sponsor":
            return super(ChildHoldWizard, self.with_context(async_mode=False)).send()
        else:
            return super().send()
