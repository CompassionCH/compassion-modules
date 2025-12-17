##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import _, fields, models


class MoveLine(models.Model):
    _inherit = "account.move.line"

    move_category = fields.Selection(related="move_id.invoice_category")

    def _update_invoice_lines_from_contract(self, modified_contract):
        """
        Takes the contract as the source to generate a write command for updating
        the invoice line
        :param modified_contract: <recurring.contract> record
        :return: list of tuples for ORM write
        """
        invoice_categories = self.mapped("move_id.invoice_category")
        if "sponsorship" in invoice_categories:
            return super()._update_invoice_lines_from_contract(modified_contract)
        else:
            # Handle gifts and Christmas fund changes here
            res = []
            for invoice_line in self:
                data_dict = {}
                gift_type = invoice_line.product_id.sponsorship_gift_type_id
                # Process specific cases for gift
                if gift_type.contract_field:
                    # Assign the price depending on the gift type
                    data_dict["price_unit"] = getattr(
                        modified_contract, gift_type.contract_field
                    )
                    # Add the modification on the line
                    res.append((1, invoice_line.id, data_dict))
            return res

    def action_sponsorship_impact(self):
        active_domain = self.env.context.get("active_domain")
        active_ids = self.env.context.get("active_ids")
        if not active_ids and not active_domain:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Warning"),
                    "message": _("No partners found in selected lines."),
                    "type": "warning",
                },
            }
        if active_ids:
            contracts = self.browse(active_ids).mapped("contract_id")
        else:
            contracts = self.search(active_domain).mapped("contract_id")
        partners = contracts.mapped("partner_id") | contracts.mapped("correspondent_id")
        return partners.open_sponsorship_report()
