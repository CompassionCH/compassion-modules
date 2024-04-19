##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Simon Gonzalez <sgonzalez@ikmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    survival_sponsorship_sale = fields.Boolean(
        default=False,
        help="The product can be sold as a survival sponsorship one"
    )
