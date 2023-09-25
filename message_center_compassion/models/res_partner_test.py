from odoo import models
from odoo.tools import config

# For the tests, we will create a mapping for res.partner object.
if config.get("test_enable"):

    class ResPartnerTest(models.Model):
        _inherit = ["compassion.mapped.model", "res.partner"]
        _name = "res.partner"
