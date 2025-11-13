##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    sponsorship_gift_type_id = fields.Many2one(
        "sponsorship.gift.type",
        "Sponsorship Gift Type",
        copy=False,
    )

    _sql_constraints = [
        (
            "sponsorship_gift_type_uniq",
            "unique(sponsorship_gift_type_id)",
            "A sponsorship gift type can only be linked to one product.",
        )
    ]

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec, vals in zip(records, vals_list, strict=True):
            if vals.get("sponsorship_gift_type_id"):
                gift_type = rec.sponsorship_gift_type_id
                if gift_type and gift_type.product_id != rec:
                    gift_type.product_id = rec
        return records

    def write(self, vals):
        result = super().write(vals)
        if "sponsorship_gift_type_id" in vals:
            for rec in self:
                gift_type = rec.sponsorship_gift_type_id
                if gift_type and gift_type.product_id != rec:
                    gift_type.product_id = rec
        return result


class Product(models.Model):
    _inherit = "product.product"

    categ_name = fields.Char(
        "Product category", related="product_tmpl_id.categ_id.name"
    )
    sponsorship_gift_type_id = fields.Many2one(
        related="product_tmpl_id.sponsorship_gift_type_id"
    )
