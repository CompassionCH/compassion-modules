##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class Product(models.Model):
    _inherit = "product.product"

    categ_name = fields.Char(
        "Product category", related="product_tmpl_id.categ_id.name", store=True
    )
