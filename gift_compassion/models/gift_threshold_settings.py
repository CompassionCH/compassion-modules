##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import math

from odoo import fields, models


class GiftThresholdSettings(models.Model):
    """Settings configuration for Compassion Gifts."""

    _name = "gift.threshold.settings"
    _description = "Gift Thresholds"

    gift_type = fields.Selection("get_gift_types", required=True)
    gift_attribution = fields.Selection("get_gift_attributions", required=True)
    sponsorship_gift_type = fields.Selection("get_sponsorship_gifts")
    min_amount = fields.Float()
    max_amount = fields.Float()
    gift_frequency = fields.Integer()
    yearly_threshold = fields.Boolean()
    currency_id = fields.Many2one("res.currency", "Currency", readonly=False)
    product_id = fields.Many2one("product.product", "Product", required=False)

    _sql_constraints = [
        (
            "unique_gift_threshold",
            "unique(gift_type,gift_attribution,sponsorship_gift_type)",
            "You already have a threshold rule for this gift",
        )
    ]

    def get_gift_types(self):
        return self.env["sponsorship.gift"].get_gift_type_selection()

    def get_gift_attributions(self):
        return self.env["sponsorship.gift"].get_gift_attributions()

    def get_sponsorship_gifts(self):
        return self.env["sponsorship.gift"].get_sponsorship_gifts()

    @staticmethod
    def _get_selection_label(selection_values, key):
        if not key:
            return ""
        return dict(selection_values).get(key, key)

    def get_sponsorship_gift_labels(self):
        return self._get_selection_label(
            self.get_sponsorship_gifts(), self.sponsorship_gift_type
        )

    def get_gift_type_label(self):
        return self._get_selection_label(self.get_gift_types(), self.gift_type)

    def get_ceiling_converted_amount(self, amount, company, date):
        raw_amount = self.currency_id._convert(
            from_amount=amount,
            to_currency=company.currency_id,
            company=company,
            date=date,
            round=False,
        )
        return f"{company.currency_id.name} {int(math.ceil(raw_amount))}"

    def get_gift_frequency_indicator(self):
        if self.yearly_threshold and self.gift_frequency == 2:
            return "*"
        if not self.yearly_threshold and self.gift_frequency == 1:
            return "**"
        return ""
