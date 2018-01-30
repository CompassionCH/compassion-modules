# -*- coding: utf-8 -*-
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


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    thanks_name = fields.Char(translate=True)
    requires_thankyou = fields.Boolean(
        'Enable thank you letter',
        help='Set to true to enable thank you letters when invoice line '
             'with this product is reconciled.',
        default=True)


class Product(models.Model):
    _inherit = 'product.product'

    thanks_name = fields.Char(related='product_tmpl_id.thanks_name')
