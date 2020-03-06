##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Stephane Eicher <seicher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    intervention_id = fields.One2many('compassion.intervention',
                                      'product_template_id',
                                      "Product's source", readonly=False)
