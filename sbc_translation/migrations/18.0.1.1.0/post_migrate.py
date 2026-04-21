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
    Ensure all existing active translator accounts are portal (share) users and
    belong to the group_user group.
    Clears any previously set home action override (action_id) since translators
    now use the portal route instead of the backend client action.
    """
    if not version:
        return

    _logger.info(
        "sbc_translation migration 18.0.1.1.0: "
        "Ensuring translator users are portal users with group_user"
    )

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        group_user = env.ref("sbc_translation.group_user", raise_if_not_found=False)

        if not group_user:
            _logger.warning("Cannot find group_user – skipping migration")
            return

        # Find all active translators
        translators = env["translation.user"].search([("active", "=", True)])
        users = translators.mapped("user_id")

        if users:
            # Clear any backend home action override and ensure group membership
            users.write(
                {
                    "action_id": False,
                    "groups_id": [(4, group_user.id)],
                }
            )
            _logger.info(
                "Updated %d translator users: cleared action_id, ensured group_user",
                len(users),
            )
