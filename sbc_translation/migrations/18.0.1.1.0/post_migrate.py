##############################################################################
#
#    Copyright (C) 2024 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Set the Translation Platform as the home action for all existing active
    translator (group_user) accounts, and promote them from share/portal users
    to internal users if needed (since group_user.share is now False).
    """
    if not version:
        return

    _logger.info(
        "sbc_translation migration 18.0.1.1.0: "
        "Setting home action for existing translator users"
    )

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        tp_action = env.ref("sbc_translation.action_translation_platform", raise_if_not_found=False)
        group_user = env.ref("sbc_translation.group_user", raise_if_not_found=False)

        if not tp_action or not group_user:
            _logger.warning(
                "Cannot find translation_platform action or group_user – skipping migration"
            )
            return

        # Find all active external translators and set home action
        translators = env["translation.user"].search([
            ("active", "=", True),
            ("user_id.share", "=", True),
        ])
        users = translators.mapped("user_id")

        if users:
            users.write({"action_id": tp_action.id})
            _logger.info(
                "Updated home action for %d translator users", len(users)
            )
