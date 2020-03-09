from odoo import models
from odoo.tools import config

if config.get("test_enable"):
    # Only register the class in testing mode
    class PartnerTest(models.Model):
        """ Test class to test the translations by making res.partner
        a translatable class."""

        _inherit = ["res.partner", "translatable.model"]
        _name = "res.partner"
