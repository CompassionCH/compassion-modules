##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Simon Gonzalez <sgonzalez@ikmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.tools import datetime

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.product"

    survival_sponsorship_sale = fields.Boolean(
        related="product_tmpl_id.survival_sponsorship_sale",
        readonly=True,
        help="(Inherited from product template) The product can be sold as a survival sponsorship one"
    )
    survival_mom_name = fields.Char(
        "Name of the mom (com)",
        help="This field is used in the communications"
    )
    survival_child_name = fields.Char(
        "Name of the baby (com)",
        help="This field is used in the communications"
    )
    survival_sponsorship_field_office_id = fields.Many2one(
        'compassion.field.office',
        string='Survival Sponsorship Field office',
        help="Define which country this product is applicable to"
    )
    slot_used = fields.Integer(
        compute="_compute_survival_slot_subscription",
        help="Number of places used (all = 100, none = 0)",
        store=True,
        readonly=True
    )
    survival_slot_number = fields.Integer(
        compute="_compute_survival_slot_subscription",
        help="Number of places available for the survival sponsorship program in a given country"
    )
    survival_sponsorship_number = fields.Integer(
        compute="_compute_survival_slot_subscription",
        help="Number of active sponsorships for the survival sponsorship program in a given country"
    )
    alltime_survival_sponsorship_number = fields.Integer(
        compute="_compute_survival_slot_subscription",
        help="Number of sponsorships for the survival sponsorship program in a given country"
    )

    _sql_constraints = [
        (
            'field_office_product_unique',
            'unique(survival_sponsorship_field_office_id)',
            'Only one product can exists for a given field office'
        ),
    ]

    @api.depends('survival_sponsorship_field_office_id', 'survival_sponsorship_sale', 'contract_line_ids')
    def _compute_survival_slot_subscription(self):
        """
        Compute the number of slot available for that country survival program
        Compute the number of sponsorships that are active on this survival country program
        """
        for product in self:
            if product.survival_sponsorship_sale and product.survival_sponsorship_field_office_id:
                product.survival_slot_number = sum(self.env['compassion.intervention'].search([
                    ('state', 'in', ['committed', 'active']),
                    ('field_office_id', '=', product.survival_sponsorship_field_office_id.id),
                    ('type', 'ilike', 'survival')
                ]).mapped('survival_slots'))

                product.alltime_survival_sponsorship_number = sum(product.contract_line_ids.mapped("quantity"))
                product.survival_sponsorship_number = sum(product.contract_line_ids.filtered(
                    lambda c: c.contract_id.state in ['active', 'waiting']
                ).mapped("quantity"))
                product.slot_used = (product.survival_sponsorship_number / product.survival_slot_number if product.survival_slot_number > 0 else 1) * 100

    @api.model
    def create_missing_products(self):
        """
        Create the new survival products for the field offices that don't have one
        This is called on installation of this module
        """
        _logger.info("Start creating products")
        # Retrieve the survival sponsorship product field offices
        ps_field_office = self.env["product.product"].search([
            ('survival_sponsorship_sale', '=', True)
        ]).mapped("survival_sponsorship_field_office_id")
        # Retrieve the current interventions
        interventions = self.env["compassion.intervention"].search([
            ("state", "not in", ['close', 'cancel']),
            ('type', 'ilike', 'survival')
        ])
        # Ensure all the informations on the interventions are up to date
        interventions.sudo().get_infos()
        # We create the product for the field offices that doesn't already have one
        for field_office in interventions.filtered(lambda i: i.field_office_id not in ps_field_office).mapped('field_office_id'):
            country = field_office.country_id
            self.env['product.product'].create(
                {
                    "name": "Survival Sponsorships",
                    "default_code": "csp_" + country.code,
                    "taxes_id": False,
                    "product_tmpl_id": self.env.ref("survival_sponsorship_compassion.survival_product_template").id,
                    "survival_sponsorship_field_office_id": field_office.id,
                    "categ_id": self.env.ref("sponsorship_compassion.product_category_fund").id,
                }
            )
            _logger.info(f"Product for {field_office.name} ({field_office.id}) created")
        _logger.info("Products creation done")

    def warn_admin(self):
        responsible_product_warn_user = self.env["res.config.settings"].sudo().get_param("survival_sponsorship_warn_user_ids")
        for product in self:
            if product.slot_used >= 80 and product.survival_sponsorship_sale:
                product.activity_schedule(
                    date_deadline=datetime.today() + relativedelta(days=7),
                    summary="Product survival limit reached.",
                    note="Some intervention should be added for the country or the sale should stop.",
                    user_id=responsible_product_warn_user
                )
