##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import config

test_mode = config.get("test_enable")


class HoldWizard(models.TransientModel):
    _inherit = "compassion.mapped.model"
    _name = "compassion.intervention.commitment.wizard"
    _description = "Intervention Commitment Wizard"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    intervention_id = fields.Many2one(
        "compassion.intervention", "Intervention", readonly=False
    )
    additional_fund_amount = fields.Float(
        related="intervention_id.requested_additional_funding"
    )
    additional_info = fields.Text(
        related="intervention_id.additional_marketing_information"
    )
    hold_id = fields.Char(related="intervention_id.hold_id")
    usd = fields.Many2one(related="intervention_id.currency_usd", readonly=False)
    commitment_amount = fields.Float(required=True)
    commit_to_additional_fund = fields.Boolean()

    @api.multi
    def commitment_created(self, intervention_vals):
        """ Called when commitment is created """
        self.intervention_id.write(
            {
                "state": "committed",
                "commitment_amount": self.commitment_amount,
                "commited_percentage": (
                    self.commitment_amount // self.intervention_id.total_cost
                )
                * 100,
                "hold_id": False,
            }
        )
        self.intervention_id.link_product()

    @api.multi
    def send_commitment(self):
        self.ensure_one()
        create_commitment = self.env.ref(
            "intervention_compassion.intervention_create_commitment_action"
        )
        # For whatever reason, we have a TransactionRollback issue with this
        # message. To avoid that, we create and process the message in two
        # steps and commit in between.
        message = self.env["gmc.message"].create(
            {"action_id": create_commitment.id, "object_id": self.id, }
        )
        if not test_mode:
            self.env.cr.commit()  # pylint: disable=invalid-commit
        message.with_context(async_mode=False).process_messages()
        if "failure" in message.state:
            raise UserError(message.failure_reason)
        return True
