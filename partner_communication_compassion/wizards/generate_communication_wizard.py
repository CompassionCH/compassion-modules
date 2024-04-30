##############################################################################
#
#    Copyright (C) 2016-2022 Compassion CH (http://www.compassion.ch)
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

    sponsorship_ids = fields.Many2many(
        "recurring.contract", string="Sponsorships", compute="_compute_sponsorships"
    )
    res_model = fields.Selection(
        [("res.partner", "Partners"), ("recurring.contract", "Sponsorships")],
        "Source",
        default="res.partner",
        required=True,
    )
    partner_source = fields.Selection(
        [
            ("partner_id", "Payer"),
            ("send_gifts_to", "Gift payer"),
            ("correspondent_id", "Correspondent"),
        ],
        "Send to",
        default="correspondent_id",
        required=True,
    )
    # Remove domain filter and handle it in the view
    model_id = fields.Many2one(domain=[], readonly=False, required=True)

    def _compute_progress(self):
        # Filter wizards related to "recurring.contract"
        s_wizards = self.filtered(lambda w: w.res_model == "recurring.contract")

        for wizard in s_wizards:
            # If a scheduled date is set, set progress to 100% directly
            if wizard.scheduled_date:
                wizard.progress = 100
            else:
                # Retrieve partners based on the specified partner source
                if wizard.partner_source == "send_gifts_to":
                    partners = wizard.sponsorship_ids.mapped(lambda s: s.send_gifts_to)
                else:
                    partners = wizard.sponsorship_ids.mapped(lambda s: getattr(s, wizard.partner_source))

                # Calculate progress as a percentage of communications sent to partners
                num_partners = len(partners)
                wizard.progress = float(len(wizard.communication_ids)) / (num_partners or 1) * 100

        # Process remaining wizards explicitly without repeating
        remaining_wizards = self - s_wizards

        for wizard in remaining_wizards:
            super(GenerateCommunicationWizard, wizard)._compute_progress()

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.depends("selection_domain", "res_model")
    def _compute_partners(self):
        if self.res_model == "recurring.contract":
            if self.partner_source == "send_gifts_to":
                # We assume the payer and the correspondent speak same lang
                partner_source = "correspondent_id"
            else:
                partner_source = self.partner_source
            if self.selection_domain:
                self.sponsorship_ids = self.env["recurring.contract"].search(
                    safe_eval(self.selection_domain)
                )
                if self.partner_source == "send_gifts_to":
                    partners = self.env["res.partner"]
                    for sponsorship in self.sponsorship_ids:
                        partners += sponsorship.mapped(sponsorship.send_gifts_to)
                else:
                    partners = self.sponsorship_ids.mapped(partner_source)
                self.partner_ids = partners
        else:
            super()._compute_partners()

    @api.depends("selection_domain", "res_model")
    def _compute_sponsorships(self):
        if self.res_model == "recurring.contract" and self.selection_domain:
            self.sponsorship_ids = self.env["recurring.contract"].search(
                safe_eval(self.selection_domain)
            )
        else:
            self.sponsorship_ids = False

    def generate_communications(self, async_mode=True):
        """Create the communication records"""
        if self.res_model == "recurring.contract":
            for sponsorship in self.sponsorship_ids:
                if self.partner_source == "send_gifts_to":
                    partner = sponsorship.mapped(sponsorship.send_gifts_to)
                else:
                    partner = sponsorship.mapped(self.partner_source)
                vals = {
                    "partner_id": partner.id,
                    "object_ids": sponsorship.id,
                    "config_id": self.model_id.id,
                }
                if self.send_mode:
                    vals.update(
                        {
                            "send_mode": self.send_mode,
                            "auto_send": False,
                        }
                    )
                options = {"force_language": self.force_language}
                if async_mode or self.scheduled_date:
                    self.with_delay(
                        eta=self.scheduled_date, priority=50
                    ).create_communication(vals, options)
                else:
                    self.create_communication(vals, options)
            return True
        else:
            return super().generate_communications(async_mode)
