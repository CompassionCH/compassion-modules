import logging
from uuid import uuid1

logger = logging.getLogger(__name__)


def post_init_hook(env):
    logger.info("Create UUID for all partners")
    for partner in env["res.partner"].search([]):
        partner.uuid = uuid1(partner.id)
