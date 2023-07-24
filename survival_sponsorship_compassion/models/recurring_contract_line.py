##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Simon Gonzalez <sgonzalez@ikmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models, api
from odoo.exceptions import UserError


class RecurringContractLine(models.Model):
    _inherit = ["recurring.contract.line"]

    product_id = fields.Many2one(
        domain="[('id', 'in', allowed_product_ids)]"
    )

    @api.constrains('quantity', 'product_id')
    def quantity_constrains(self):
        for contract_line in self.filtered("product_id.survival_sponsorship_sale"):
            product = contract_line.product_id
            qty_reached = contract_line.quantity + product.survival_sponsorship_number
            if qty_reached > product.survival_slot_number:
                raise UserError("You can't validate a contract that uses more slot than the one available\n"
                                f"{product.survival_sponsorship_field_office_id.name} has "
                                f"{product.survival_slot_number} slots available "
                                f"you tried to add {contract_line.quantity}\n"
                                f"{product.survival_slot_number - product.survival_sponsorship_number} slots "
                                f"are still available")

    @api.onchange("contract_type")
    def onchange_type(self):
        """ Change domain of product depending on type of contract. """
        res = super().onchange_type()
        if self.contract_id.type == "CSP":
            tmpl = self.env.ref(
                "survival_sponsorship_compassion.survival_product_template")
            res["domain"] = {
                "product_id": [
                    ("product_tmpl_id", "=", tmpl.id)
                ]
            }
        return res
