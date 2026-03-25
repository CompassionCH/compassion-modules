from odoo import api, fields, models


class SponsorshipGiftType(models.Model):
    _name = "sponsorship.gift.type"
    _description = "Sponsorship Gift Type"

    name = fields.Char(required=True)
    code = fields.Char(required=True, copy=False)
    product_id = fields.Many2one(
        "product.template", "Product", domain=[("type", "=", "service")], copy=False
    )
    gmc_gift_type = fields.Selection(
        [
            ("Project Gift", "Project Gift"),
            ("Family Gift", "Family Gift"),
            ("Beneficiary Gift", "Participant Gift"),
        ]
    )
    gmc_attribution = fields.Selection(
        [
            ("Center Based Programming", "CDSP"),
            ("Home Based Programming (Survival & Early Childhood)", "CSP"),
            ("Sponsored Child Family", "Sponsored Child Family"),
            ("Sponsorship", "Sponsorship"),
            ("Survival", "Survival"),
            ("Survival Neediest Families", "Neediest Families"),
            ("Survival Neediest Families - Split", "Neediest Families Split"),
        ]
    )
    gmc_sponsorship_gift_type = fields.Selection(
        [
            ("Birthday", "Birthday"),
            ("General", "General"),
            ("Graduation/Final", "Graduation/Final"),
        ]
    )
    contract_field = fields.Char()

    _sql_constraints = [
        (
            "sponsorship_gift_type_code_uniq",
            "unique(code)",
            "The code of the sponsorship gift type must be unique.",
        ),
        (
            "sponsorship_gift_type_product_uniq",
            "unique(product_id)",
            "A sponsorship gift type can only be linked to one product.",
        ),
        (
            "contract_field_uniq",
            "unique(contract_field)",
            "The contract field must be unique.",
        ),
    ]

    @api.constrains("contract_field")
    def _validate_contract_field(self):
        for record in self:
            if record.contract_field:
                if record.contract_field not in self.env["recurring.contract"]._fields:
                    raise ValueError(
                        f"The field '{record.contract_field}' does not exist on the "
                        f"model 'recurring.contract'."
                    )
                field_type = (
                    self.env["recurring.contract"]._fields[record.contract_field].type
                )
                if field_type not in ("float", "monetary", "integer"):
                    raise ValueError(
                        f"The field '{record.contract_field}' "
                        f"must be a monetary or amount."
                    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec, vals in zip(records, vals_list, strict=True):
            if vals.get("product_id"):
                product = rec.product_id
                if product and product.sponsorship_gift_type_id != rec:
                    product.sponsorship_gift_type_id = rec
        return records

    def write(self, vals):
        result = super().write(vals)
        if "product_id" in vals:
            for rec in self:
                product = rec.product_id
                if product and product.sponsorship_gift_type_id != rec:
                    product.sponsorship_gift_type_id = rec
        return result
