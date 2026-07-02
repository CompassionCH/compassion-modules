from openupgradelib import openupgrade

from odoo import SUPERUSER_ID
from odoo.api import Environment


def migrate(cr, version):
    env = Environment(cr, SUPERUSER_ID, {})
    openupgrade.load_data(
        env,
        "child_compassion",
        "data/ir_cron.xml",
    )
