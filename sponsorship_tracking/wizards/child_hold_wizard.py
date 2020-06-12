##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import date

from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import relativedelta


class ChildHoldWizard(models.TransientModel):
    """ Add return action for sub_sponsorship. """

    _inherit = "child.hold.wizard"

    return_action = fields.Selection(selection_add=[("sub", "Make SUB Sponsorship")])

    @api.multi
    def send(self):
        """ Remove default_type from context to avoid putting type in child.
        For SUB, put async mode to False in order to wait for the message
        answers.
        """
        async_mode = self.env.context.get("async_mode", self.return_action != "sub")
        context_copy = self.env.context.copy()
        context_copy["async_mode"] = async_mode
        if "default_type" in context_copy:
            del context_copy["default_type"]
        return super(ChildHoldWizard, self.with_context(context_copy)).send()

    def _get_action(self, holds):
        action = super()._get_action(holds)
        if self.return_action == "sub":
            sub_contract = self.env["recurring.contract"].browse(
                self.env.context.get("contract_id")
            )
            # Prevent choosing child completing in less than 2 years
            in_two_years = date.today() + relativedelta(years=2)
            child = holds[0].child_id
            if child.completion_date and child.completion_date < in_two_years:
                raise UserError(
                    _(
                        "Completion date of child is in less than 2 years! "
                        "Please choose another child."
                    )
                )
            sub_contract.write({"child_id": child.id})
            sub_contract.next_invoice_date = self.env.context.get("next_invoice_date")
            action.update(
                {
                    "res_model": "recurring.contract",
                    "res_id": sub_contract.id,
                    "view_mode": "form",
                }
            )
            action["context"] = self.with_context({"default_type": "S", }).env.context
        return action
