import uuid
from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for partner in env["res.partner"].search([("active", "in", [True, False])]):
        partner.uuid = uuid.uuid4()
