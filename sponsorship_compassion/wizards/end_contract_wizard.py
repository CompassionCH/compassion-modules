##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo.addons.child_compassion.models.compassion_hold import HoldType

from odoo import models, fields, api


class EndContractWizard(models.TransientModel):
    _inherit = "end.contract.wizard"

    keep_child_on_hold = fields.Boolean()
    hold_expiration_date = fields.Datetime(
        default=lambda s: s.env["compassion.hold"].get_default_hold_expiration(
            HoldType.SPONSOR_CANCEL_HOLD
        ),
        required=True,
    )

    @api.multi
    def end_contract(self):
        self.ensure_one()
        super().end_contract()

        for contract in self.contract_ids.filtered("child_id"):
            child = contract.child_id
            child.child_unsponsored()
            if self.keep_child_on_hold:
                if child.hold_id:
                    # Update the hold
                    child.hold_id.write(
                        {
                            "type": HoldType.SPONSOR_CANCEL_HOLD.value,
                            "expiration_date": self.hold_expiration_date,
                        }
                    )
                else:
                    # Setup a hold expiration in the sponsorship
                    contract.hold_expiration_date = self.hold_expiration_date
            else:
                # Setup the hold expiration now
                contract.hold_expiration_date = fields.Datetime.now()
                # Remove the hold on the child
                if child.hold_id:
                    child.hold_id.release_hold()
        return True
