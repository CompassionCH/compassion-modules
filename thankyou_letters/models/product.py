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

    partner_communication_config = fields.Many2one(
        'partner.communication.config', 'Thank you config', required=False)

    thanks_name = fields.Char(translate=True)
    requires_thankyou = fields.Boolean(
        'Enable thank you letter',
        help='Set to true to enable thank you letters when invoice line '
             'with this product is reconciled.',
        default=True)
    success_story_id = fields.Many2one(
        'success.story', 'Success story',
        help='Forces a success story when receiving a donation for this '
             'product.'
    )


class Product(models.Model):
    _inherit = 'product.product'

    thanks_name = fields.Char(related='product_tmpl_id.thanks_name')
    success_story_id = fields.Many2one(
        related='product_tmpl_id.success_story_id')
