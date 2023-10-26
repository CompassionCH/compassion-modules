# -*- coding: utf-8 -*-

import os
from os.path import join as opj

from odoo import api, fields, models, tools


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
    contract_id = fields.Many2one("recurring.contract", string="sponsorship", readonly=True)
    sub_sponsorship_id = fields.Many2one("recurring.contract", string="Sub sponsorship", readonly=True)
    parent_id = fields.Many2one("recurring.contract", string="Previous sponsorship", readonly=True)
    child_id = fields.Many2one("compassion.child", string="Child", readonly=True)
    company_id = fields.Many2one("res.company", string="Company", readonly=True)
    pricelist_id = fields.Many2one("product.pricelist", string="Pricelist", readonly=False)
    medium_id = fields.Many2one("utm.medium", string="Medium", readonly=True)
    end_reason_id = fields.Many2one("recurring.contract.end.reason", string="End reason", readonly=True)
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
    activation_date = fields.Date("Activation date", readonly=True)

    def init(self):
        script = opj(os.path.dirname(__file__), "spn_info.sql")
        with open(script) as f:
            tools.drop_view_if_exists(self.env.cr, "spn_info")
            self.env.cr.execute(f.read())
