##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models


class MoveLine(models.Model):
    """Add salespersons to invoice_lines."""

    _inherit = "account.move.line"

    user_id = fields.Many2one("res.partner", "Ambassador", readonly=False)
    event_id = fields.Many2one(
        "crm.event.compassion",
        "Event",
        related="analytic_account_id.event_id",
        store=True,
        readonly=True,
    )

    @api.onchange("contract_id")
    def on_change_contract_id(self):
        """Push Ambassador to invoice line."""
        if self.contract_id.ambassador_id:
            self.user_id = self.contract_id.ambassador_id

    def generate_thank_you(self):
        """
        - Include a receipt for Ambassadors when generating thank you letters
        - Do not group communications which have not the same event linked.
        - Propagate event to the communication and use the creator of the event
        as the default thanker.
        """
        events = self.mapped("event_id")
        if not events:
            return super().generate_thank_you()

        # separate move lines by event
        event_mapping = {
            event: self.filtered(lambda ivl, ev=event: ivl.event_id == ev)
            for event in events
        }
        generated_comm_ids = []
        for event, move_lines in event_mapping.items():
            default_communication_config = event.communication_config_id
            # Special case for gifts : never put in event donation
            if "gift" in move_lines.mapped("move_id.invoice_category"):
                default_communication_config = False
            generated_comm_ids += super(
                MoveLine,
                move_lines.with_context(
                    same_job_search=[("event_id", "=", event.id)],
                    default_event_id=event.id,
                    default_user_id=event.user_id.id,
                    default_communication_config=default_communication_config,
                ),
            ).generate_thank_you()

            # Generate ambassador receipts
            if event.ambassador_config_id:
                ambassador_mapping = {
                    ambassador: move_lines.filtered(
                        lambda ivl, amb=ambassador: ivl.user_id == amb
                    )
                    for ambassador in move_lines.mapped("user_id").filtered(
                        "receive_ambassador_receipts"
                    )
                }
                ambassador_receipts = self.env["partner.communication.job"]
                for ambassador, donations in ambassador_mapping.items():
                    if "gift" not in donations.mapped("move_id.invoice_category"):
                        ambassador_receipts += ambassador_receipts.create(
                            {
                                "partner_id": ambassador.id,
                                "object_ids": donations.ids,
                                "config_id": event.ambassador_config_id.id,
                            }
                        )
                if ambassador_receipts:
                    # Delay the sending in case an ambassador receives several donations
                    # Five minutes of delay should be enough.
                    ambassador_receipts.with_delay(priority=100, eta=60 * 5).send()
        return generated_comm_ids
