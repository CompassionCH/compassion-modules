##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import _, models
from odoo.exceptions import UserError

from .product_names import GIFT_PRODUCTS_REF, PRODUCT_GIFT_CHRISTMAS


class MoveLine(models.Model):
    _inherit = "account.move.line"

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
                # Process specific cases for gift
                if invoice_line.product_id.default_code == PRODUCT_GIFT_CHRISTMAS:
                    gift_type = "christmas_invoice"
                elif invoice_line.product_id.default_code == GIFT_PRODUCTS_REF[0]:
                    gift_type = "birthday_invoice"
                else:
                    raise UserError(
                        _("Unexpected error while updating contract invoices.")
                    )
                # Assign the price depending on the gift type
                data_dict["price_unit"] = getattr(modified_contract, gift_type)
                # Add the modification on the line
                res.append((1, invoice_line.id, data_dict))
            return res
