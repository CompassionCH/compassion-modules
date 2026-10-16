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
        compute="_compute_event",
        store=True,
    )

    @api.depends("analytic_line_ids", "contract_id.origin_id.event_id")
    def _compute_event(self):
        """The event of a line, once set, is kept. Otherwise it is found from:
        - the origin of the sponsorship of the line;
        - the UTM of the invoice: the event whose source it is, or the
          peer-to-peer event whose campaign it is;
        - the analytic accounts of the line (history: the accounts of events
          migrated from v14 are in other plans, each in its own column)."""
        event_obj = self.env["crm.event.compassion"]
        analytic_obj = self.env["account.analytic.account"]
        move_utm = "source_id" in self.env["account.move"]._fields
        for line in self:
            if line.event_id:
                line.event_id = line.event_id
                continue
            event = line.contract_id.origin_id.event_id
            if not event and move_utm and line.move_id.source_id:
                event = event_obj.search(
                    [("source_id", "=", line.move_id.source_id.id)], limit=1
                )
            if not event and move_utm and line.move_id.campaign_id:
                events = event_obj.search(
                    [("campaign_id", "=", line.move_id.campaign_id.id)], limit=2
                )
                event = events if len(events) == 1 else event
            if not event:
                event = analytic_obj.union(
                    *(al._get_analytic_accounts() for al in line.analytic_line_ids)
                ).mapped("event_id")[:1]
            line.event_id = event

    @api.onchange("contract_id")
    def on_change_contract_id(self):
        """Push Ambassador to invoice line."""
        if self.contract_id.ambassador_id:
            self.user_id = self.contract_id.ambassador_id

    def unlink(self):
        # The analytic lines left on these items are deleted by the database
        # (ondelete cascade), without account.analytic.line.unlink().
        events = self.analytic_line_ids._get_events()
        res = super().unlink()
        events._recompute_expenses()
        return res

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
        return generated_comm_ids
