# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    thanks_name = fields.Char(translate=True)


class Product(models.Model):
    _inherit = 'product.product'

    thanks_name = fields.Char(related='product_tmpl_id.thanks_name')
