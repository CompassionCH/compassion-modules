import logging
from uuid import uuid1

from odoo import SUPERUSER_ID, api

logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    logger.info("Create UUID for all partners")

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        for partner in env["res.partner"].search([]):
            partner.uuid = uuid1(partner.id)
