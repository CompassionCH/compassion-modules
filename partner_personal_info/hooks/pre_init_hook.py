import logging

from openupgradelib import openupgrade

logger = logging.getLogger(__name__)


def pre_init_hook(env):
    logger.info("Create UUID for all partners")
    if not openupgrade.column_exists(env.cr, "res_partner", "uuid"):
        openupgrade.add_columns(
            env,
            [
                (
                    "res.partner",
                    "uuid",
                    "char",
                    False,
                ),
            ],
        )
    env.cr.execute(
        """
                   UPDATE res_partner
SET uuid = gen_random_uuid()
WHERE uuid IS NULL;"""
    )
