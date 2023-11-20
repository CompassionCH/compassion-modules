##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    def get_donations(self):
        """
        Gets a tuple for thank_you communication
        If more than one product, product_name is False
        :return: (total_donation_amount, product_name)
        """
        res_name = False
        total = sum(self.mapped("price_subtotal"))
        total_string = f"{int(total):,}".replace(",", "'")

        product_names = self.mapped("product_id.thanks_name")
        if len(product_names) == 1:
            res_name = product_names[0]

        return total_string, res_name

    def generate_thank_you(self):
        """
        Creates a thank you letter communication.
        Must be called only on a single partner at a time.
        """
        new_invoice_lines = self.filtered("product_id.requires_thankyou")
        if not new_invoice_lines:
            # Avoid generating thank you if no valid invoice lines are present
            return "Product is not thankable"

        new_communication_config = self.env.context.get("default_communication_config")
        if not new_communication_config:
            product_configs = new_invoice_lines.mapped(
                "product_id.partner_communication_config"
            )
            if len(product_configs) == 1:
                new_communication_config = product_configs[0]
            else:
                _logger.warning(
                    f"{len(product_configs)} product thank you config found, "
                    f"falling back to the default"
                )
                new_communication_config = self.env.ref(
                    "thankyou_letters.config_thankyou_standard"
                )

        partner = self.mapped("partner_id")
        partner.ensure_one()

        all_thanks_config_ids = (
            self.env["partner.communication.config"]
            .search([("send_mode_pref_field", "like", "thankyou_preference")])
            .ids
        )

        all_existing_comm = self.env["partner.communication.job"].search(
            [
                ("partner_id", "=", partner.id),
                ("state", "in", ("call", "pending")),
                ("config_id", "in", all_thanks_config_ids),
            ]
            + self.env.context.get("same_job_search", [])
        )

        all_invoice_lines = new_invoice_lines
        if all_existing_comm:
            all_invoice_lines |= all_existing_comm.get_objects()

        thankyou_config = (
            self.env["thankyou.config"].search([]).for_donation(all_invoice_lines)
        )
        generated_comms = self.env["partner.communication.job"]
        if not thankyou_config:
            return False
        for communication_config in new_communication_config | all_existing_comm.mapped(
            "config_id"
        ):
            invoice_lines = (
                new_invoice_lines
                if new_communication_config == communication_config
                else self.env[self._name]
            )

            existing_comm = all_existing_comm.filtered(
                lambda x, cf=communication_config: x.config_id.id == cf.id
            )

            if existing_comm:
                invoice_lines |= existing_comm.get_objects()

            send_mode, auto_mode = thankyou_config.build_inform_mode(
                partner, communication_config.print_if_not_email
            )

            comm_vals = {
                "partner_id": partner.id,
                "config_id": communication_config.id,
                "object_ids": invoice_lines.ids,
                "need_call": thankyou_config.need_call
                or communication_config.need_call,
                "print_subject": False,
                "user_id": self.env.context.get("default_user_id")
                or thankyou_config.user_id.id,
                "send_mode": send_mode,
                "auto_send": auto_mode,
            }
            success_stories = invoice_lines.mapped("product_id.success_story_id")
            if success_stories:
                existing_comm = existing_comm.with_context(
                    default_success_story_id=success_stories[0].id
                )

            if existing_comm:
                existing_comm.write(comm_vals)
                existing_comm.refresh_text()
            else:
                existing_comm = existing_comm.create(comm_vals)

            if new_communication_config == communication_config:
                self.mapped("move_id").write({"communication_id": existing_comm.id})
            generated_comms += existing_comm
        return generated_comms.ids
