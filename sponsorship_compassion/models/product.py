##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields
# Name of gifts products
GIFT_REF = ["gift_birthday", "gift_gen", "gift_family", "gift_project",
            "gift_graduation"]


class Product(models.Model):
    _inherit = 'product.product'

    categ_name = fields.Char(
        'Product category', related='product_tmpl_id.categ_id.name',
        store=True)
