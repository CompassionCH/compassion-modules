import os
from os.path import join as opj

from odoo import api, fields, models, tools


class MisSpnInfoSettings(models.TransientModel):
    """Settings configuration for reporting."""

    _inherit = "res.config.settings"

    mis_main_company_id = fields.Many2one(
        "res.company",
        string="Main reporting Company",
    )
    mis_child_sponsored_id = fields.Many2one(
        "account.account",
        "Child Sponsored account",
        domain=[
            ("user_type_id.include_initial_balance", "=", True),
        ],  # ("company_id", "=", mis_main_company_id.id),
    )
    mis_contract_created_id = fields.Many2one(
        "account.account",
        "Contract Created account",
        domain=[
            ("user_type_id.include_initial_balance", "=", True),
        ],
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        config = self.env["ir.config_parameter"].sudo()
        res["mis_contract_created_id"] = int(
            config.get_param("mis_contract_created_id", default="0")
        )
        res["mis_child_sponsored_id"] = int(
            config.get_param("mis_child_sponsored_id", default="0")
        )
        res["mis_main_company_id"] = int(
            config.get_param("mis_main_company_id", default="0")
        )
        return res

    @api.model
    def set_values(self):
        self.env["ir.config_parameter"].set_param(
            "mis_contract_created_id", self.mis_contract_created_id.id
        )
        self.env["ir.config_parameter"].set_param(
            "mis_child_sponsored_id", self.mis_child_sponsored_id.id
        )
        self.env["ir.config_parameter"].set_param(
            "mis_main_company_id", self.mis_main_company_id.id
        )
        super().set_values()


class MisSpnInfo(models.Model):
    _name = "mis.spn.info"
    _description = "MIS Sponsorship acquisition info"
    _auto = False
    account_id = fields.Many2one(
        comodel_name="account.account", string="Account", readonly=True
    )
    date = fields.Date()
    partner_id = fields.Many2one("res.partner", string="Partner", readonly=True)
    correspondent_id = fields.Many2one("res.partner", string="Partner", readonly=True)
    contract_id = fields.Many2one(
        "recurring.contract", string="sponsorship", readonly=True
    )
    sub_sponsorship_id = fields.Many2one(
        "recurring.contract", string="Sub sponsorship", readonly=True
    )
    parent_id = fields.Many2one(
        "recurring.contract", string="Previous sponsorship", readonly=True
    )
    child_id = fields.Many2one("compassion.child", string="Child", readonly=True)
    report_company_id = fields.Many2one(
        "res.company", string="Reporting Company", readonly=True
    )
    pricelist_id = fields.Many2one(
        "product.pricelist", string="Pricelist", readonly=False
    )

    medium_id = fields.Many2one("utm.medium", string="Medium", readonly=True)
    end_reason_id = fields.Many2one(
        "recurring.contract.end.reason", string="End reason", readonly=True
    )
    source_id = fields.Many2one("utm.source", string="Source", readonly=True)
    campaign_id = fields.Many2one("utm.campaign", string="Campaign", readonly=True)
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True)
    analytic_id = fields.Many2one(
        "account.analytic.account", string="Analytic account", readonly=True
    )
    company_id = fields.Many2one(
        comodel_name="res.company", string="Company", readonly=True
    )
    credit = fields.Float()
    sponsorship_line_id = fields.Integer()
    debit = fields.Float()
    amount_currency = fields.Monetary(
        string="Amount in Currency",
        store=True,
        copy=True,
        help="The amount expressed in an optional other currency if it is a "
        "multi-currency entry.",
    )
    activation_date = fields.Date("Activation date", readonly=True)

    def init(self):
        param_obj = self.env["ir.config_parameter"]
        mis_contract_created_id = param_obj.get_param("mis_contract_created_id")
        mis_main_company_id = self.env["res.company"].browse(
            param_obj.get_param("mis_main_company_id")
        )
        mis_child_sponsored_id = param_obj.get_param("mis_child_sponsored_id")
        script = opj(os.path.dirname(__file__), "spn_info.sql")
        currency = (
            self.env["res.company"]
            .search([("id", "=", mis_main_company_id.id)])
            .currency_id.id
        )
        with open(script) as f:
            tools.drop_view_if_exists(self.env.cr, "mid_spn_info")
            sql = f.read() % (
                mis_child_sponsored_id,
                currency,
                mis_main_company_id.id,
                mis_child_sponsored_id,
                currency,
                mis_main_company_id.id,
                mis_contract_created_id,
                currency,
                mis_main_company_id.id,
                mis_contract_created_id,
                currency,
                mis_main_company_id.id,
            )
            self.env.cr.execute(sql)
