##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class GenerateCommunicationWizard(models.TransientModel):
    _inherit = "partner.communication.generate.wizard"

    success_story_id = fields.Many2one(
        "success.story",
        "Success Story",
        domain=[("type", "=", "story")],
        readonly=False,
    )
    print_subject = fields.Boolean(default=True)
    print_header = fields.Boolean()

    # A single Many2many field for selecting one or multiple invoices
    selected_move_line_ids = fields.Many2many(
        "account.move.line",
        string="Invoices",
        help="User-selected invoices for communication generation.",
    )
    res_model = fields.Selection(
        selection_add=[("account.move", "Invoices")],
        ondelete={"account.move": "cascade"},
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get("active_model") == "account.move":
            invoice_ids = self.env.context.get("active_ids", [])
            if invoice_ids:
                invoices = self.env["account.move"].browse(invoice_ids)
                res["res_model"] = "account.move"
                # Pre-fill selected_move_line_ids with the chosen invoice IDs
                res["selected_move_line_ids"] = [(6, 0, invoices.invoice_line_ids.ids)]
        return res

    @api.depends("selection_domain", "res_model")
    def _compute_partners(self):
        if self.res_model == "account.move":
            # For invoices, we need to compute partners from selected move lines
            invoice_ids = self.env["account.move"].search_read(
                safe_eval(self.selection_domain), ["partner_id", "line_ids"]
            )
            line_ids = map(lambda inv: inv["line_ids"], invoice_ids)
            move_line_ids = [mvl for sublist in line_ids for mvl in sublist]
            self.selected_move_line_ids = [(6, 0, move_line_ids)]
            self.partner_ids = [
                (
                    6,
                    0,
                    [inv["partner_id"][0] for inv in invoice_ids if inv["partner_id"]],
                )
            ]
            return True
        else:
            return super()._compute_partners()

    def generate_communications(self, async_mode=True):
        if self.res_model == "account.move":
            if not self.selected_move_line_ids:
                # No invoices selected, do nothing or fallback
                _logger.info("No invoices selected; skipping generation.")
                return super().generate_communications(async_mode)

            # Generate communications for each invoice
            for move_line in self.selected_move_line_ids:
                vals = {
                    "partner_id": move_line.partner_id.id,
                    "object_ids": move_line.id,
                    "config_id": self.model_id.id,
                }
                if self.send_mode:
                    vals.update({"send_mode": self.send_mode, "auto_send": False})
                options = {"force_language": self.force_language}

                if async_mode or self.scheduled_date:
                    self.with_delay_sh(
                        "create_communication",
                        vals,
                        options,
                        channel="root.partner_communication",
                        eta=self.scheduled_date,
                        priority=50,
                        identity_key=f"{self._name}.create_comm.invoice.{move_line.id}",
                    )
                else:
                    self.create_communication(vals, options)

            return True
        else:
            return super().generate_communications(async_mode)

    def generate(self):
        return super(
            GenerateCommunicationWizard,
            self.with_context(
                default_print_subject=self.print_subject,
                default_print_header=self.print_header,
                default_success_story_id=self.success_story_id.id,
            ),
        ).generate()
